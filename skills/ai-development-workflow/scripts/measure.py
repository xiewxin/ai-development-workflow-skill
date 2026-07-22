#!/usr/bin/env python3
"""提供 AI 開發工作流程的本機參考計時命令。"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from typing import Any, BinaryIO, TextIO
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


class MeasureError(Exception):
    """表示可安全回傳給呼叫端的計量錯誤。"""

    def __init__(self, code: str, message: str) -> None:
        """保存穩定錯誤碼與繁體中文訊息。"""
        super().__init__(message)
        self.code = code
        self.message = message


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


def complete_action(mixed_work: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
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
        by_phase = {
            phase: interval_seconds(
                [interval for interval in state["intervals"] if interval["phase"] == phase]
            )
            for phase in PHASES
        }
        summary: dict[str, Any] = {
            "id": state["id"],
            "state": "completed",
            "source": state["provider"],
            "seconds": sum(by_phase.values()),
            "phases": by_phase,
            "confidence": confidence,
            "anomalies": anomalies,
            "mixed_work": mixed_work,
        }
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
                complete_action(arguments.mixed_work),
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
            raise MeasureError("not_implemented", "人工參考基準尚未實作")
        emit(result, stdout)
        return 0
    except MeasureError as error:
        emit({"code": error.code, "error": error.message}, stdout)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
