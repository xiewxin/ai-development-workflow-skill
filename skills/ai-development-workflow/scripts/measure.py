#!/usr/bin/env python3
"""提供 AI 開發工作流程的本機參考計時命令。"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import math
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
import time
from typing import Any, BinaryIO, TextIO
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import uuid


COMMANDS = (
    "start",
    "baseline",
    "enter",
    "pause",
    "resume",
    "recover",
    "complete",
    "status",
    "delete",
)
PHASES = (
    "requirement_plan",
    "test_design",
    "implementation",
    "verification_fix",
    "docs_review",
)
SCHEMA_VERSION = 1
ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
ACTIVITYWATCH_DEFAULT_URL = urlunsplit(("http", "localhost:5600", "", "", ""))
ACTIVITYWATCH_TIMEOUT_SECONDS = 2
ACTIVITYWATCH_MAX_RESPONSE_BYTES = 2 * 1024 * 1024


class MeasureError(Exception):
    """表示可安全回傳給呼叫端的計量錯誤。"""

    def __init__(self, code: str, message: str) -> None:
        """保存穩定錯誤碼與繁體中文訊息。"""
        super().__init__(message)
        self.code = code
        self.message = message


class ActivityWatchError(Exception):
    """表示 ActivityWatch 無法安全提供可用聚合。"""


class LoopbackRedirectHandler(HTTPRedirectHandler):
    """只允許 ActivityWatch 請求導向另一個 loopback HTTP 位址。"""

    def redirect_request(
        self,
        request: Request,
        file_pointer: Any,
        code: int,
        message: str,
        headers: Any,
        new_url: str,
    ) -> Request | None:
        """導向前先驗證新位址，阻擋外部主機。"""
        try:
            validate_activitywatch_base_url(new_url)
        except ActivityWatchError as error:
            raise URLError("ActivityWatch redirect rejected") from error
        return super().redirect_request(
            request,
            file_pointer,
            code,
            message,
            headers,
            new_url,
        )


class SafeArgumentParser(argparse.ArgumentParser):
    """將 argparse 錯誤轉為精簡 JSON，而非終止程序。"""

    def error(self, message: str) -> None:
        """以穩定錯誤碼回報無效參數。"""
        raise MeasureError("invalid_arguments", f"命令參數無效：{message}")


class FileLock:
    """以標準函式庫提供跨平台非阻塞排他鎖。"""

    def __init__(self, path: Path) -> None:
        """記錄鎖檔路徑。"""
        self.path = path
        self.handle: BinaryIO | None = None

    def __enter__(self) -> "FileLock":
        """取得排他鎖，衝突時不等待。"""
        self.path.touch(mode=0o600, exist_ok=True)
        if os.name != "nt":
            os.chmod(self.path, 0o600)
        self.handle = self.path.open("r+b")
        if self.path.stat().st_size == 0:
            self.handle.write(b"0")
            self.handle.flush()
        try:
            if os.name == "nt":
                import msvcrt

                self.handle.seek(0)
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            self.handle.close()
            self.handle = None
            raise MeasureError("state_locked", "計量狀態正由其他程序更新") from error
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        """釋放排他鎖並關閉檔案。"""
        if self.handle is None:
            return
        try:
            if os.name == "nt":
                import msvcrt

                self.handle.seek(0)
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
        finally:
            self.handle.close()
            self.handle = None


def build_parser() -> SafeArgumentParser:
    """建立不含搜尋或跨對話恢復能力的命令解析器。"""
    parser = SafeArgumentParser(prog="measure.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start")
    start.add_argument("--phase", choices=PHASES, required=True)
    start.add_argument("--provider", choices=("session", "activitywatch"), default="session")

    baseline = subparsers.add_parser("baseline")
    baseline.add_argument("--id", required=True)
    baseline.add_argument("--estimate", action="append", default=[])

    enter = subparsers.add_parser("enter")
    enter.add_argument("--id", required=True)
    enter.add_argument("--phase", choices=PHASES, required=True)

    for command in ("pause", "resume", "status"):
        child = subparsers.add_parser(command)
        child.add_argument("--id", required=True)

    recover = subparsers.add_parser("recover")
    recover.add_argument("--id", required=True)
    recover.add_argument("--exclude-open", action="store_true")

    complete = subparsers.add_parser("complete")
    complete.add_argument("--id", required=True)
    complete.add_argument("--mixed-work", choices=("no", "yes", "unknown"), required=True)

    delete = subparsers.add_parser("delete")
    delete.add_argument("--id", required=True)
    delete.add_argument("--allow-active", action="store_true")
    delete.add_argument("--confirm")
    return parser


def is_within(path: Path, parent: Path) -> bool:
    """判斷 path 是否等於或位於 parent 下。"""
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def git_root(cwd: Path) -> Path | None:
    """唯讀取得目前 Git 工作樹根目錄。"""
    result = subprocess.run(
        ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip()).resolve()


def default_state_dir(environment: dict[str, str]) -> Path:
    """依平台慣例選擇預設本機狀態目錄。"""
    if environment.get("XDG_STATE_HOME"):
        return Path(environment["XDG_STATE_HOME"]) / "ai-development-workflow"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "ai-development-workflow"
    if os.name == "nt":
        local_app_data = environment.get("LOCALAPPDATA")
        if not local_app_data:
            raise MeasureError("unsafe_state_dir", "Windows 缺少安全的本機狀態目錄")
        return Path(local_app_data) / "ai-development-workflow"
    return Path.home() / ".local" / "state" / "ai-development-workflow"


def resolve_state_dir(
    environment: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> Path:
    """解析並驗證不位於工作樹內的安全狀態目錄。"""
    environment = dict(os.environ if environment is None else environment)
    cwd = Path.cwd() if cwd is None else cwd
    custom = environment.get("AI_WORKFLOW_STATE_DIR")
    candidate = Path(custom) if custom else default_state_dir(environment)
    resolved = candidate.expanduser().resolve(strict=False)
    root = git_root(cwd)
    if root is not None and is_within(resolved, root):
        raise MeasureError("unsafe_state_dir", "計量狀態目錄不得位於 Git 工作樹內")
    if os.name == "nt" and custom:
        local_app_data = environment.get("LOCALAPPDATA")
        if not local_app_data or not is_within(resolved, Path(local_app_data).resolve(strict=False)):
            raise MeasureError("unsafe_state_dir", "Windows 自訂狀態目錄必須位於目前使用者資料範圍")
    resolved.mkdir(mode=0o700, parents=True, exist_ok=True)
    if os.name != "nt":
        mode = resolved.stat().st_mode & 0o777
        if mode & 0o022:
            raise MeasureError("unsafe_state_dir", "計量狀態目錄不可開放群組或其他使用者寫入")
        os.chmod(resolved, 0o700)
    return resolved


def validate_id(measurement_id: str) -> str:
    """拒絕可能逃逸狀態目錄的計量 ID。"""
    if not ID_PATTERN.fullmatch(measurement_id):
        raise MeasureError("invalid_id", "計量 ID 格式無效")
    return measurement_id


def state_path(state_dir: Path, measurement_id: str) -> Path:
    """取得已驗證 ID 的狀態檔路徑。"""
    return state_dir / f"{validate_id(measurement_id)}.json"


def lock_path(state_dir: Path, measurement_id: str) -> Path:
    """取得已驗證 ID 的鎖檔路徑。"""
    return state_dir / f"{validate_id(measurement_id)}.lock"


def read_state(path: Path) -> dict[str, Any]:
    """讀取狀態並拒絕損壞或版本不符的內容。"""
    if not path.is_file():
        raise MeasureError("state_not_found", "找不到指定計量狀態")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise MeasureError("state_corrupt", "計量狀態損壞，已保留原檔") from error
    if not isinstance(payload, dict) or payload.get("version") != SCHEMA_VERSION:
        raise MeasureError("state_corrupt", "計量狀態版本或結構無效，已保留原檔")
    return payload


def write_state(path: Path, state: dict[str, Any]) -> None:
    """以同目錄暫存檔與原子取代安全更新狀態。"""
    descriptor, temporary_name = tempfile.mkstemp(prefix=".measure-", dir=str(path.parent))
    temporary = Path(temporary_name)
    try:
        if os.name != "nt":
            os.chmod(temporary, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(state, handle, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        if os.name != "nt":
            os.chmod(path, 0o600)
    except (OSError, TypeError, ValueError) as error:
        try:
            temporary.unlink(missing_ok=True)
        finally:
            raise MeasureError("state_write_failed", "計量狀態寫入失敗，已保留原檔") from error


def interval_seconds(intervals: list[dict[str, Any]]) -> int:
    """驗證並加總已閉合區間秒數。"""
    total = 0.0
    for interval in intervals:
        start = float(interval["start"])
        end = float(interval["end"])
        if end < start:
            raise MeasureError("state_corrupt", "計量區間時間順序無效")
        total += end - start
    return round(total)


def validate_intervals(intervals: list[dict[str, Any]]) -> None:
    """驗證所有已閉合區間的階段與時間不重疊。"""
    normalized: list[tuple[float, float]] = []
    try:
        for interval in intervals:
            if interval["phase"] not in PHASES:
                raise MeasureError("state_corrupt", "計量區間階段無效")
            start = float(interval["start"])
            end = float(interval["end"])
            if not math.isfinite(start) or not math.isfinite(end) or end < start:
                raise MeasureError("state_corrupt", "計量區間時間順序無效")
            normalized.append((start, end))
    except (KeyError, TypeError, ValueError) as error:
        raise MeasureError("state_corrupt", "計量區間結構無效") from error
    previous_end: float | None = None
    for start, end in sorted(normalized):
        if previous_end is not None and start < previous_end:
            raise MeasureError("state_corrupt", "計量區間不得重疊")
        previous_end = end


def format_utc(timestamp: float) -> str:
    """將 epoch 秒數轉為 ActivityWatch 可用的 UTC 時間。"""
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat().replace("+00:00", "Z")


def parse_utc(value: str) -> float:
    """解析 ActivityWatch UTC 時間。"""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as error:
        raise ActivityWatchError("ActivityWatch 事件時間無效") from error
    if parsed.tzinfo is None:
        raise ActivityWatchError("ActivityWatch 事件缺少時區")
    return parsed.timestamp()


def validate_activitywatch_base_url(value: str) -> str:
    """驗證並正規化只指向 loopback 的 HTTP 位址。"""
    try:
        parsed = urlsplit(value)
        port = parsed.port or 5600
    except ValueError as error:
        raise ActivityWatchError("ActivityWatch 位址無效") from error
    if (
        parsed.scheme != "http"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in ("", "/")
    ):
        raise ActivityWatchError("ActivityWatch 只允許 loopback HTTP 位址")
    try:
        addresses = {
            info[4][0]
            for info in socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)
        }
        if not addresses or not all(ipaddress.ip_address(address).is_loopback for address in addresses):
            raise ActivityWatchError("ActivityWatch 主機不是 loopback")
    except (OSError, ValueError) as error:
        raise ActivityWatchError("ActivityWatch loopback 位址無法驗證") from error
    hostname = parsed.hostname
    host = f"[{hostname}]" if ":" in hostname else hostname
    return urlunsplit(("http", f"{host}:{port}", "", "", ""))


def fetch_activitywatch_json(url: str) -> Any:
    """以固定逾時與唯讀 GET 讀取本機 ActivityWatch JSON。"""
    try:
        request = Request(url, method="GET")
        with build_opener(LoopbackRedirectHandler()).open(
            request,
            timeout=ACTIVITYWATCH_TIMEOUT_SECONDS,
        ) as response:
            final_url = response.geturl()
            validate_activitywatch_base_url(
                urlunsplit((*urlsplit(final_url)[:2], "", "", ""))
            )
            payload = response.read(ACTIVITYWATCH_MAX_RESPONSE_BYTES + 1)
        if len(payload) > ACTIVITYWATCH_MAX_RESPONSE_BYTES:
            raise ActivityWatchError("ActivityWatch 回應過大")
        return json.loads(payload.decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ActivityWatchError("ActivityWatch API 不可用") from error


def merge_ranges(ranges: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """合併半開時間區間，避免重複累計。"""
    merged: list[list[float]] = []
    for start, end in sorted(ranges):
        if not math.isfinite(start) or not math.isfinite(end) or end < start:
            raise ActivityWatchError("ActivityWatch 事件區間無效")
        if end == start:
            continue
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return [(start, end) for start, end in merged]


def intersect_seconds(
    left: list[tuple[float, float]],
    right: list[tuple[float, float]],
) -> int:
    """以雙指標加總兩組已合併區間的交集秒數。"""
    left_index = 0
    right_index = 0
    total = 0.0
    while left_index < len(left) and right_index < len(right):
        left_start, left_end = left[left_index]
        right_start, right_end = right[right_index]
        total += max(0.0, min(left_end, right_end) - max(left_start, right_start))
        if left_end <= right_end:
            left_index += 1
        else:
            right_index += 1
    return round(total)


def activitywatch_phase_seconds(
    intervals: list[dict[str, Any]],
    configured_url: str,
) -> dict[str, int]:
    """讀取 AFK 活躍事件並按階段聚合 session 交集。"""
    base_url = validate_activitywatch_base_url(configured_url)
    buckets = fetch_activitywatch_json(f"{base_url}/api/0/buckets/")
    if not isinstance(buckets, dict):
        raise ActivityWatchError("ActivityWatch bucket 回應結構無效")
    hostname = socket.gethostname()
    candidates = [
        bucket_id
        for bucket_id, metadata in buckets.items()
        if isinstance(bucket_id, str)
        and isinstance(metadata, dict)
        and metadata.get("type") == "afkstatus"
        and metadata.get("client") == "aw-watcher-afk"
        and metadata.get("hostname") == hostname
    ]
    if len(candidates) != 1:
        raise ActivityWatchError("ActivityWatch AFK bucket 無法唯一確定")
    session_ranges = merge_ranges(
        [(float(interval["start"]), float(interval["end"])) for interval in intervals]
    )
    if not session_ranges:
        return {phase: 0 for phase in PHASES}
    query = urlencode(
        {
            "start": format_utc(session_ranges[0][0]),
            "end": format_utc(session_ranges[-1][1]),
        }
    )
    bucket_id = quote(candidates[0], safe="")
    events = fetch_activitywatch_json(
        f"{base_url}/api/0/buckets/{bucket_id}/events?{query}"
    )
    if not isinstance(events, list):
        raise ActivityWatchError("ActivityWatch event 回應結構無效")
    active_ranges: list[tuple[float, float]] = []
    for event in events:
        if not isinstance(event, dict) or not isinstance(event.get("data"), dict):
            raise ActivityWatchError("ActivityWatch event 結構無效")
        if event["data"].get("status") != "not-afk":
            continue
        try:
            start = parse_utc(event["timestamp"])
            duration = float(event["duration"])
        except (KeyError, TypeError, ValueError) as error:
            raise ActivityWatchError("ActivityWatch 活躍事件無效") from error
        if not math.isfinite(duration) or duration < 0:
            raise ActivityWatchError("ActivityWatch 事件時長無效")
        active_ranges.append((start, start + duration))
    active = merge_ranges(active_ranges)
    return {
        phase: intersect_seconds(
            merge_ranges(
                [
                    (float(interval["start"]), float(interval["end"]))
                    for interval in intervals
                    if interval["phase"] == phase
                ]
            ),
            active,
        )
        for phase in PHASES
    }


def parse_estimates(items: list[str]) -> dict[str, list[int]]:
    """解析並驗證五個固定階段的 PERT 秒數。"""
    estimates: dict[str, list[int]] = {}
    for item in items:
        if "=" not in item:
            raise MeasureError("invalid_baseline", "PERT 格式必須是 phase=O,M,P")
        phase, raw_values = item.split("=", 1)
        if phase not in PHASES or phase in estimates:
            raise MeasureError("invalid_baseline", "PERT 階段未知或重複")
        parts = raw_values.split(",")
        if len(parts) != 3:
            raise MeasureError("invalid_baseline", "每個 PERT 階段必須包含 O、M、P")
        if not all(re.fullmatch(r"\d+", value) for value in parts):
            raise MeasureError("invalid_baseline", "PERT 數值必須是非負整數秒")
        numbers = [int(value) for value in parts]
        if not numbers[0] <= numbers[1] <= numbers[2]:
            raise MeasureError("invalid_baseline", "PERT 必須滿足 O <= M <= P")
        estimates[phase] = numbers
    if set(estimates) != set(PHASES):
        raise MeasureError("invalid_baseline", "PERT 必須涵蓋全部固定階段")
    return {phase: estimates[phase] for phase in PHASES}


def expected_phase_seconds(estimates: dict[str, list[int]]) -> dict[str, int]:
    """依 PERT 公式計算各階段人工參考秒數。"""
    return {
        phase: round((values[0] + 4 * values[1] + values[2]) / 6)
        for phase, values in estimates.items()
    }


def calculate_baseline_fingerprint(
    estimates: dict[str, list[int]],
    locked_at: float,
) -> str:
    """以正規化數值與鎖定時間計算基準指紋。"""
    canonical = json.dumps(
        {"estimates": estimates, "locked_at": locked_at},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def brief_payload(state: dict[str, Any]) -> dict[str, Any]:
    """建立例行命令使用的精簡輸出。"""
    return {
        "id": state["id"],
        "state": state["state"],
        "phase": state["phase"],
        "seconds": interval_seconds(state["intervals"]),
        "anomalies": state["anomalies"],
    }


def close_open_interval(state: dict[str, Any], current_time: float) -> None:
    """閉合目前區間並寫入 interval 清單。"""
    opened = state.get("open")
    if not isinstance(opened, dict):
        raise MeasureError("state_corrupt", "running 狀態缺少開啟區間")
    started_at = float(opened["start"])
    if current_time < started_at:
        raise MeasureError("clock_reversed", "系統時間倒退，未更新計量狀態")
    state["intervals"].append(
        {"phase": opened["phase"], "start": started_at, "end": current_time}
    )
    state["open"] = None


def start_measurement(state_dir: Path, phase: str, provider: str, current_time: float) -> dict[str, Any]:
    """建立新的 running 計量狀態。"""
    measurement_id = uuid.uuid4().hex
    path = state_path(state_dir, measurement_id)
    with FileLock(lock_path(state_dir, measurement_id)):
        state = {
            "version": SCHEMA_VERSION,
            "id": measurement_id,
            "provider": provider,
            "state": "running",
            "phase": phase,
            "open": {"phase": phase, "start": current_time},
            "intervals": [],
            "baseline": None,
            "anomalies": [],
            "confidence": "medium",
            "completed_summary": None,
        }
        write_state(path, state)
    return brief_payload(state)


def update_measurement(
    state_dir: Path,
    measurement_id: str,
    action: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    """在排他鎖內讀取、更新並原子寫入狀態。"""
    path = state_path(state_dir, measurement_id)
    with FileLock(lock_path(state_dir, measurement_id)):
        state = read_state(path)
        result = action(state)
        write_state(path, state)
        return result


def pause_action(current_time: float) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """建立 pause 狀態轉換。"""
    def action(state: dict[str, Any]) -> dict[str, Any]:
        if state["state"] == "paused":
            return brief_payload(state)
        if state["state"] != "running":
            raise MeasureError("invalid_transition", "目前狀態不能暫停")
        close_open_interval(state, current_time)
        state["state"] = "paused"
        return brief_payload(state)

    return action


def resume_action(current_time: float) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """建立 resume 狀態轉換。"""
    def action(state: dict[str, Any]) -> dict[str, Any]:
        if state["state"] == "running":
            return brief_payload(state)
        if state["state"] != "paused":
            raise MeasureError("invalid_transition", "目前狀態不能恢復")
        state["state"] = "running"
        state["open"] = {"phase": state["phase"], "start": current_time}
        return brief_payload(state)

    return action


def enter_action(phase: str, current_time: float) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """建立切換固定階段的狀態轉換。"""
    def action(state: dict[str, Any]) -> dict[str, Any]:
        if state["state"] not in ("running", "paused"):
            raise MeasureError("invalid_transition", "目前狀態不能切換階段")
        if state["phase"] == phase:
            return brief_payload(state)
        if state["state"] == "running":
            close_open_interval(state, current_time)
            state["open"] = {"phase": phase, "start": current_time}
        state["phase"] = phase
        return brief_payload(state)

    return action


def recover_action(exclude_open: bool) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """建立排除未閉合區間的中斷恢復。"""
    def action(state: dict[str, Any]) -> dict[str, Any]:
        if not exclude_open:
            raise MeasureError("confirmation_required", "恢復時必須明確排除未閉合區間")
        if state["state"] == "paused":
            return brief_payload(state)
        if state["state"] != "running":
            raise MeasureError("invalid_transition", "目前狀態不能執行中斷恢復")
        state["open"] = None
        state["state"] = "paused"
        if "open_interval_excluded" not in state["anomalies"]:
            state["anomalies"].append("open_interval_excluded")
        state["confidence"] = "low"
        return brief_payload(state)

    return action


def baseline_action(
    estimates: dict[str, list[int]],
    current_time: float,
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """建立一次性鎖定 PERT 人工參考基準的更新。"""
    def action(state: dict[str, Any]) -> dict[str, Any]:
        if state["state"] not in ("running", "paused"):
            raise MeasureError("invalid_transition", "目前狀態不能鎖定人工參考基準")
        existing = state.get("baseline")
        if isinstance(existing, dict):
            if existing.get("estimates") != estimates:
                raise MeasureError("baseline_locked", "人工參考基準已鎖定，不得修改")
            return {
                "id": state["id"],
                "state": state["state"],
                "baseline_seconds": existing["seconds"],
                "baseline_fingerprint": existing["fingerprint"],
            }
        implementation_intervals = [
            interval
            for interval in state["intervals"]
            if interval["phase"] == "implementation"
            and float(interval["end"]) > float(interval["start"])
        ]
        opened = state.get("open")
        if implementation_intervals or (
            isinstance(opened, dict) and opened.get("phase") == "implementation"
        ):
            raise MeasureError("baseline_too_late", "產品實作開始後不得倒推人工參考基準")
        phase_seconds = expected_phase_seconds(estimates)
        baseline_seconds = sum(phase_seconds.values())
        if baseline_seconds <= 0:
            raise MeasureError("invalid_baseline", "人工參考基準必須大於零")
        locked_at = float(current_time)
        fingerprint = calculate_baseline_fingerprint(estimates, locked_at)
        state["baseline"] = {
            "estimates": estimates,
            "phase_seconds": phase_seconds,
            "seconds": baseline_seconds,
            "locked_at": locked_at,
            "fingerprint": fingerprint,
        }
        return {
            "id": state["id"],
            "state": state["state"],
            "baseline_seconds": baseline_seconds,
            "baseline_fingerprint": fingerprint,
        }

    return action


def complete_action(
    mixed_work: str,
    activitywatch_url: str = ACTIVITYWATCH_DEFAULT_URL,
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """建立完成封存與聚合摘要。"""
    def action(state: dict[str, Any]) -> dict[str, Any]:
        if state["state"] == "completed":
            return state["completed_summary"]
        if state["state"] != "paused":
            raise MeasureError("invalid_transition", "完成前必須先暫停或排除開啟區間")
        confidence = state["confidence"]
        anomalies = list(state["anomalies"])
        if mixed_work != "no":
            confidence = "low"
            anomaly = f"mixed_work_{mixed_work}"
            if anomaly not in anomalies:
                anomalies.append(anomaly)
        validate_intervals(state["intervals"])
        by_phase = {
            phase: interval_seconds(
                [interval for interval in state["intervals"] if interval["phase"] == phase]
            )
            for phase in PHASES
        }
        source = "session"
        if state["provider"] == "activitywatch":
            try:
                by_phase = activitywatch_phase_seconds(
                    state["intervals"],
                    activitywatch_url,
                )
                source = "activitywatch"
            except ActivityWatchError:
                confidence = "low"
                if "activitywatch_fallback" not in anomalies:
                    anomalies.append("activitywatch_fallback")
        summary: dict[str, Any] = {
            "id": state["id"],
            "state": "completed",
            "source": source,
            "seconds": sum(by_phase.values()),
            "phases": by_phase,
            "confidence": confidence,
            "anomalies": anomalies,
            "mixed_work": mixed_work,
        }
        baseline = state.get("baseline")
        if isinstance(baseline, dict):
            expected_fingerprint = calculate_baseline_fingerprint(
                baseline["estimates"],
                float(baseline["locked_at"]),
            )
            if expected_fingerprint != baseline.get("fingerprint"):
                confidence = "low"
                if "baseline_fingerprint_mismatch" not in anomalies:
                    anomalies.append("baseline_fingerprint_mismatch")
                summary["confidence"] = confidence
                summary["anomalies"] = anomalies
            else:
                baseline_seconds = int(baseline["seconds"])
                saved_seconds = baseline_seconds - int(summary["seconds"])
                summary.update(
                    {
                        "baseline_seconds": baseline_seconds,
                        "baseline_fingerprint": baseline["fingerprint"],
                        "saved_seconds": saved_seconds,
                        "efficiency_percent": round(saved_seconds / baseline_seconds * 100, 2),
                    }
                )
        state["state"] = "completed"
        state["confidence"] = confidence
        state["anomalies"] = anomalies
        state["completed_summary"] = summary
        return summary

    return action


def delete_measurement(
    state_dir: Path,
    measurement_id: str,
    allow_active: bool,
    confirmation: str | None,
) -> dict[str, str]:
    """刪除已完成或經雙重確認的活動狀態。"""
    path = state_path(state_dir, measurement_id)
    lock = lock_path(state_dir, measurement_id)
    with FileLock(lock):
        state = read_state(path)
        if state["state"] != "completed" and not (
            allow_active and confirmation == "DELETE-ACTIVE"
        ):
            raise MeasureError("confirmation_required", "活動狀態需要雙重確認才能刪除")
        path.unlink()
    return {"id": measurement_id, "state": "deleted"}


def status_measurement(state_dir: Path, measurement_id: str) -> dict[str, Any]:
    """在不修改狀態下回傳精簡摘要。"""
    path = state_path(state_dir, measurement_id)
    with FileLock(lock_path(state_dir, measurement_id)):
        return brief_payload(read_state(path))


def emit(payload: dict[str, Any], stdout: TextIO) -> None:
    """以緊湊單行 JSON 輸出結果。"""
    stdout.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")


def main(
    argv: Sequence[str] | None = None,
    *,
    now: Callable[[], float] = time.time,
    stdout: TextIO = sys.stdout,
) -> int:
    """執行參考計時命令並輸出精簡 JSON。"""
    try:
        arguments = build_parser().parse_args(list(argv) if argv is not None else None)
        state_dir = resolve_state_dir()
        current_time = float(now())
        if arguments.command == "start":
            result = start_measurement(
                state_dir,
                arguments.phase,
                arguments.provider,
                current_time,
            )
        elif arguments.command == "pause":
            result = update_measurement(
                state_dir,
                arguments.id,
                pause_action(current_time),
            )
        elif arguments.command == "resume":
            result = update_measurement(
                state_dir,
                arguments.id,
                resume_action(current_time),
            )
        elif arguments.command == "enter":
            result = update_measurement(
                state_dir,
                arguments.id,
                enter_action(arguments.phase, current_time),
            )
        elif arguments.command == "recover":
            result = update_measurement(
                state_dir,
                arguments.id,
                recover_action(arguments.exclude_open),
            )
        elif arguments.command == "complete":
            result = update_measurement(
                state_dir,
                arguments.id,
                complete_action(
                    arguments.mixed_work,
                    os.environ.get(
                        "AI_WORKFLOW_ACTIVITYWATCH_URL",
                        ACTIVITYWATCH_DEFAULT_URL,
                    ),
                ),
            )
        elif arguments.command == "baseline":
            estimates = parse_estimates(arguments.estimate)
            result = update_measurement(
                state_dir,
                arguments.id,
                baseline_action(estimates, current_time),
            )
        elif arguments.command == "status":
            result = status_measurement(state_dir, arguments.id)
        elif arguments.command == "delete":
            result = delete_measurement(
                state_dir,
                arguments.id,
                arguments.allow_active,
                arguments.confirm,
            )
        else:
            raise MeasureError("invalid_arguments", "未知計量命令")
        emit(result, stdout)
        return 0
    except MeasureError as error:
        emit({"code": error.code, "error": error.message}, stdout)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
