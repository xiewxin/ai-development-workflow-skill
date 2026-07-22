from __future__ import annotations

import importlib.util
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "ai-development-workflow" / "scripts" / "measure.py"


class FakeClock:
    """提供可重現的測試時間。"""

    def __init__(self) -> None:
        self.value = 1_753_156_800.0

    def now(self) -> float:
        """回傳目前測試時間。"""
        return self.value

    def advance(self, seconds: float) -> None:
        """推進指定秒數。"""
        self.value += seconds


def load_measure():
    """以獨立 module 載入待測 CLI。"""
    spec = importlib.util.spec_from_file_location("ai_workflow_measure", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class MeasureCliTest(unittest.TestCase):
    """驗證參考計時 CLI 的狀態合同。"""

    def setUp(self) -> None:
        """為每個案例建立獨立狀態目錄與時鐘。"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.state_dir = Path(self.temp_dir.name) / "state"
        self.clock = FakeClock()
        self.measure = load_measure()
        self.activitywatch_url: str | None = None

    def run_cli(self, *arguments: str) -> tuple[int, dict[str, object], bytes]:
        """執行 CLI 並回傳 exit code、JSON 與原始輸出。"""
        output = io.StringIO()
        environment = {
            "AI_WORKFLOW_STATE_DIR": str(self.state_dir),
            "LOCALAPPDATA": self.temp_dir.name,
        }
        if self.activitywatch_url is not None:
            environment["AI_WORKFLOW_ACTIVITYWATCH_URL"] = self.activitywatch_url
        with patch.dict(os.environ, environment, clear=False):
            exit_code = self.measure.main(list(arguments), now=self.clock.now, stdout=output)
        raw = output.getvalue().encode("utf-8")
        return exit_code, json.loads(raw), raw

    def start(self, provider: str = "session") -> str:
        """建立計量並回傳 ID。"""
        code, payload, _ = self.run_cli(
            "start",
            "--phase",
            "requirement_plan",
            "--provider",
            provider,
        )
        self.assertEqual(0, code)
        return str(payload["id"])

    def valid_estimate_arguments(self) -> list[str]:
        """回傳涵蓋全部固定階段的有效 PERT 參數。"""
        return [
            "--estimate",
            "requirement_plan=600,900,1200",
            "--estimate",
            "test_design=300,600,900",
            "--estimate",
            "implementation=1800,2700,4200",
            "--estimate",
            "verification_fix=600,1200,2400",
            "--estimate",
            "docs_review=300,600,900",
        ]

    def lock_baseline(self, measurement_id: str) -> dict[str, object]:
        """鎖定標準測試 PERT 並回傳摘要。"""
        code, payload, _ = self.run_cli(
            "baseline",
            "--id",
            measurement_id,
            *self.valid_estimate_arguments(),
        )
        self.assertEqual(0, code)
        return payload

    def start_activitywatch_server(
        self,
        *,
        buckets: object,
        events: object,
        buckets_status: int = 200,
        redirect: str | None = None,
        delay: float = 0,
    ) -> tuple[list[tuple[str, str]], str]:
        """啟動只用於測試的 ActivityWatch 假服務。"""
        requests: list[tuple[str, str]] = []

        class Handler(BaseHTTPRequestHandler):
            """記錄方法與路徑，並回傳預設的 JSON。"""

            def do_GET(self) -> None:
                """處理唯讀測試請求。"""
                requests.append(("GET", self.path))
                if delay:
                    time.sleep(delay)
                if redirect is not None and self.path.startswith("/api/0/buckets/"):
                    self.send_response(302)
                    self.send_header("Location", redirect)
                    self.end_headers()
                    return
                if self.path == "/api/0/buckets/":
                    self.send_json(buckets_status, buckets)
                    return
                if self.path.startswith("/api/0/buckets/") and "/events?" in self.path:
                    self.send_json(200, events)
                    return
                self.send_json(404, {"error": "not found"})

            def do_POST(self) -> None:
                """記錄並拒絕非唯讀請求。"""
                requests.append(("POST", self.path))
                self.send_json(405, {"error": "method not allowed"})

            def send_json(self, status: int, payload: object) -> None:
                """輸出測試 JSON 回應。"""
                body = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: object) -> None:
                """關閉測試服務的預設日誌。"""

        server = ThreadingHTTPServer(("localhost", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        port = int(server.server_address[1])
        return requests, urlunsplit(("http", f"localhost:{port}", "", "", ""))

    def test_start_pause_resume_complete_and_delete_lifecycle(self) -> None:
        """正常生命週期只累計閉合工作區間。"""
        measurement_id = self.start()
        self.clock.advance(90)
        self.assertEqual(
            "paused",
            self.run_cli("pause", "--id", measurement_id)[1]["state"],
        )
        self.assertEqual(
            "running",
            self.run_cli("resume", "--id", measurement_id)[1]["state"],
        )
        self.clock.advance(30)
        self.run_cli("pause", "--id", measurement_id)
        code, completed, raw = self.run_cli(
            "complete",
            "--id",
            measurement_id,
            "--mixed-work",
            "no",
        )
        self.assertEqual(0, code)
        self.assertEqual("completed", completed["state"])
        self.assertEqual(120, completed["seconds"])
        self.assertLessEqual(len(raw), 1024)
        self.assertEqual(
            "deleted",
            self.run_cli("delete", "--id", measurement_id)[1]["state"],
        )
        self.assertEqual(2, self.run_cli("status", "--id", measurement_id)[0])

    def test_parser_has_no_cross_conversation_discovery_commands(self) -> None:
        """命令面不得提供跨對話搜尋或解析能力。"""
        self.assertEqual(
            {
                "start",
                "baseline",
                "enter",
                "pause",
                "resume",
                "recover",
                "complete",
                "status",
                "delete",
            },
            set(self.measure.COMMANDS),
        )

    def test_idempotent_transitions_do_not_duplicate_time(self) -> None:
        """重複 pause、resume 與同階段 enter 不得重複累計。"""
        measurement_id = self.start()
        self.clock.advance(15)
        self.run_cli("enter", "--id", measurement_id, "--phase", "requirement_plan")
        self.run_cli("pause", "--id", measurement_id)
        self.run_cli("pause", "--id", measurement_id)
        self.run_cli("resume", "--id", measurement_id)
        self.run_cli("resume", "--id", measurement_id)
        self.clock.advance(5)
        self.run_cli("pause", "--id", measurement_id)
        completed = self.run_cli(
            "complete",
            "--id",
            measurement_id,
            "--mixed-work",
            "no",
        )[1]
        self.assertEqual(20, completed["seconds"])

    def test_running_measurement_requires_pause_before_complete(self) -> None:
        """尚有開啟區間時不得完成計量。"""
        measurement_id = self.start()
        code, payload, _ = self.run_cli(
            "complete",
            "--id",
            measurement_id,
            "--mixed-work",
            "no",
        )
        self.assertEqual(2, code)
        self.assertEqual("invalid_transition", payload["code"])

    def test_recover_excludes_open_interval_and_lowers_confidence(self) -> None:
        """中斷恢復應丟棄未閉合區間並記錄異常。"""
        measurement_id = self.start()
        self.clock.advance(300)
        recovered = self.run_cli(
            "recover",
            "--id",
            measurement_id,
            "--exclude-open",
        )[1]
        self.assertEqual("paused", recovered["state"])
        completed = self.run_cli(
            "complete",
            "--id",
            measurement_id,
            "--mixed-work",
            "no",
        )[1]
        self.assertEqual(0, completed["seconds"])
        self.assertEqual("low", completed["confidence"])
        self.assertIn("open_interval_excluded", completed["anomalies"])

    def test_active_delete_requires_two_explicit_flags(self) -> None:
        """活動中狀態只能以雙重確認刪除。"""
        measurement_id = self.start()
        self.assertEqual(2, self.run_cli("delete", "--id", measurement_id)[0])
        self.assertEqual(
            2,
            self.run_cli(
                "delete",
                "--id",
                measurement_id,
                "--allow-active",
            )[0],
        )
        deleted = self.run_cli(
            "delete",
            "--id",
            measurement_id,
            "--allow-active",
            "--confirm",
            "DELETE-ACTIVE",
        )[1]
        self.assertEqual("deleted", deleted["state"])

    def test_state_is_private_and_contains_no_project_identity(self) -> None:
        """狀態檔應限制權限且不保存專案或需求識別。"""
        code, started, raw = self.run_cli(
            "start",
            "--phase",
            "requirement_plan",
            "--provider",
            "session",
        )
        self.assertEqual(0, code)
        self.assertLessEqual(len(raw), 200)
        measurement_id = str(started["id"])
        state_file = self.state_dir / f"{measurement_id}.json"
        serialized = state_file.read_text(encoding="utf-8")
        self.assertNotIn(str(ROOT), serialized)
        for forbidden in (
            '"repo"',
            '"path"',
            '"prompt"',
            '"commit"',
            '"window"',
            '"application"',
        ):
            self.assertNotIn(forbidden, serialized)
        if os.name != "nt":
            self.assertEqual(0o700, self.state_dir.stat().st_mode & 0o777)
            self.assertEqual(0o600, state_file.stat().st_mode & 0o777)

    def test_state_directory_inside_worktree_is_rejected(self) -> None:
        """狀態目錄不得直接位於目前 Git 工作樹。"""
        self.state_dir = ROOT / ".unsafe-measure-state"
        code, payload, _ = self.run_cli(
            "start",
            "--phase",
            "requirement_plan",
            "--provider",
            "session",
        )
        self.assertEqual(2, code)
        self.assertEqual("unsafe_state_dir", payload["code"])
        self.assertFalse(self.state_dir.exists())

    @unittest.skipIf(os.name == "nt", "Windows symlink 權限由平台另外驗證")
    def test_symlink_resolving_into_worktree_is_rejected(self) -> None:
        """symlink 解析後落入工作樹時也應拒絕。"""
        link = Path(self.temp_dir.name) / "linked-root"
        link.symlink_to(ROOT, target_is_directory=True)
        self.state_dir = link / ".unsafe-measure-state"
        code, payload, _ = self.run_cli(
            "start",
            "--phase",
            "requirement_plan",
            "--provider",
            "session",
        )
        self.assertEqual(2, code)
        self.assertEqual("unsafe_state_dir", payload["code"])

    @unittest.skipIf(os.name == "nt", "POSIX mode 不適用 Windows")
    def test_group_writable_state_directory_is_rejected(self) -> None:
        """既有狀態目錄不可開放群組或其他使用者寫入。"""
        self.state_dir.mkdir(mode=0o700)
        self.state_dir.chmod(0o770)
        code, payload, _ = self.run_cli(
            "start",
            "--phase",
            "requirement_plan",
            "--provider",
            "session",
        )
        self.assertEqual(2, code)
        self.assertEqual("unsafe_state_dir", payload["code"])

    def test_corrupt_state_is_preserved(self) -> None:
        """損壞狀態應停止計量且保留原始證據。"""
        measurement_id = self.start()
        state_file = self.state_dir / f"{measurement_id}.json"
        corrupt = "{invalid-json"
        state_file.write_text(corrupt, encoding="utf-8")
        code, payload, _ = self.run_cli("status", "--id", measurement_id)
        self.assertEqual(2, code)
        self.assertEqual("state_corrupt", payload["code"])
        self.assertEqual(corrupt, state_file.read_text(encoding="utf-8"))

    def test_clock_reversal_does_not_modify_state(self) -> None:
        """系統時間倒退時應拒絕更新並保留狀態。"""
        measurement_id = self.start()
        state_file = self.state_dir / f"{measurement_id}.json"
        before = state_file.read_bytes()
        self.clock.value -= 1
        code, payload, _ = self.run_cli("pause", "--id", measurement_id)
        self.assertEqual(2, code)
        self.assertEqual("clock_reversed", payload["code"])
        self.assertEqual(before, state_file.read_bytes())

    def test_lock_conflict_does_not_modify_state(self) -> None:
        """同一 ID 同時更新時只有持鎖程序可寫入。"""
        measurement_id = self.start()
        state_file = self.state_dir / f"{measurement_id}.json"
        before = state_file.read_bytes()
        lock_file = self.state_dir / f"{measurement_id}.lock"
        with self.measure.FileLock(lock_file):
            code, payload, _ = self.run_cli("pause", "--id", measurement_id)
        self.assertEqual(2, code)
        self.assertEqual("state_locked", payload["code"])
        self.assertEqual(before, state_file.read_bytes())

    def test_atomic_replace_failure_preserves_previous_state(self) -> None:
        """原子取代失敗時應保留原檔並轉為安全錯誤。"""
        measurement_id = self.start()
        state_file = self.state_dir / f"{measurement_id}.json"
        before = state_file.read_bytes()
        state = self.measure.read_state(state_file)
        caught: Exception | None = None
        with patch.object(self.measure.os, "replace", side_effect=OSError("replace failed")):
            try:
                self.measure.write_state(state_file, state)
            except Exception as error:  # noqa: BLE001 - 測試需驗證公開錯誤類型
                caught = error
        self.assertIsInstance(caught, self.measure.MeasureError)
        self.assertEqual("state_write_failed", caught.code)
        self.assertEqual(before, state_file.read_bytes())

    def test_pert_baseline_and_efficiency_are_reproducible(self) -> None:
        """固定 PERT 與閉合區間應產生可重現提效摘要。"""
        measurement_id = self.start()
        self.clock.advance(100)
        self.run_cli("pause", "--id", measurement_id)
        baseline = self.lock_baseline(measurement_id)
        self.assertEqual(6200, baseline["baseline_seconds"])
        self.assertEqual(64, len(str(baseline["baseline_fingerprint"])))

        self.run_cli("enter", "--id", measurement_id, "--phase", "test_design")
        self.run_cli("resume", "--id", measurement_id)
        self.clock.advance(100)
        self.run_cli("pause", "--id", measurement_id)
        self.run_cli("enter", "--id", measurement_id, "--phase", "implementation")
        self.run_cli("resume", "--id", measurement_id)
        self.clock.advance(100)
        self.run_cli("pause", "--id", measurement_id)

        completed = self.run_cli(
            "complete",
            "--id",
            measurement_id,
            "--mixed-work",
            "no",
        )[1]
        self.assertEqual(300, completed["seconds"])
        self.assertEqual(6200, completed["baseline_seconds"])
        self.assertEqual(5900, completed["saved_seconds"])
        self.assertEqual(95.16, completed["efficiency_percent"])
        self.assertEqual("medium", completed["confidence"])

    def test_baseline_is_idempotent_but_cannot_be_changed(self) -> None:
        """相同基準可重送，不同基準在鎖定後應拒絕。"""
        measurement_id = self.start()
        first = self.lock_baseline(measurement_id)
        self.clock.advance(50)
        second = self.lock_baseline(measurement_id)
        self.assertEqual(first, second)
        changed = self.valid_estimate_arguments()
        changed[1] = "requirement_plan=700,900,1200"
        code, payload, _ = self.run_cli(
            "baseline",
            "--id",
            measurement_id,
            *changed,
        )
        self.assertEqual(2, code)
        self.assertEqual("baseline_locked", payload["code"])

    def test_baseline_cannot_be_created_after_implementation_time(self) -> None:
        """產品實作已開始後不得倒推人工參考基準。"""
        measurement_id = self.start()
        self.run_cli("enter", "--id", measurement_id, "--phase", "implementation")
        self.clock.advance(1)
        self.run_cli("pause", "--id", measurement_id)
        code, payload, _ = self.run_cli(
            "baseline",
            "--id",
            measurement_id,
            *self.valid_estimate_arguments(),
        )
        self.assertEqual(2, code)
        self.assertEqual("baseline_too_late", payload["code"])

    def test_invalid_pert_values_are_rejected(self) -> None:
        """PERT 應拒絕缺階段、負數、非有限值與順序錯誤。"""
        invalid_argument_sets = (
            self.valid_estimate_arguments()[:-2],
            [
                *self.valid_estimate_arguments()[:-2],
                "--estimate",
                "docs_review=-1,0,1",
            ],
            [
                *self.valid_estimate_arguments()[:-2],
                "--estimate",
                "docs_review=2,1,3",
            ],
            [
                *self.valid_estimate_arguments()[:-2],
                "--estimate",
                "docs_review=0,nan,1",
            ],
            [
                *self.valid_estimate_arguments()[:-2],
                "--estimate",
                "docs_review=0,0.5,1",
            ],
        )
        for arguments in invalid_argument_sets:
            with self.subTest(arguments=arguments):
                measurement_id = self.start()
                code, payload, _ = self.run_cli(
                    "baseline",
                    "--id",
                    measurement_id,
                    *arguments,
                )
                self.assertEqual(2, code)
                self.assertEqual("invalid_baseline", payload["code"])

    def test_overlapping_intervals_are_rejected(self) -> None:
        """狀態中的重疊區間應停止完成，避免重複計時。"""
        measurement_id = self.start()
        self.clock.advance(20)
        self.run_cli("pause", "--id", measurement_id)
        state_file = self.state_dir / f"{measurement_id}.json"
        state = self.measure.read_state(state_file)
        first = dict(state["intervals"][0])
        state["intervals"].append(
            {
                "phase": "test_design",
                "start": first["start"] + 10,
                "end": first["end"] + 10,
            }
        )
        self.measure.write_state(state_file, state)
        code, payload, _ = self.run_cli(
            "complete",
            "--id",
            measurement_id,
            "--mixed-work",
            "no",
        )
        self.assertEqual(2, code)
        self.assertEqual("state_corrupt", payload["code"])

    def test_full_summary_and_routine_output_stay_compact(self) -> None:
        """含基準的完整摘要與例行輸出仍應簡短。"""
        measurement_id = self.start()
        self.clock.advance(1)
        self.run_cli("pause", "--id", measurement_id)
        _, _, status_raw = self.run_cli("status", "--id", measurement_id)
        self.assertLessEqual(len(status_raw), 200)
        self.lock_baseline(measurement_id)
        _, completed, completed_raw = self.run_cli(
            "complete",
            "--id",
            measurement_id,
            "--mixed-work",
            "unknown",
        )
        self.assertIn("efficiency_percent", completed)
        self.assertLessEqual(len(completed_raw), 1024)

    def test_mixed_work_lowers_confidence(self) -> None:
        """混入其他工作或無法判定時應降低可信度。"""
        for mixed_work in ("yes", "unknown"):
            with self.subTest(mixed_work=mixed_work):
                measurement_id = self.start()
                self.run_cli("pause", "--id", measurement_id)
                completed = self.run_cli(
                    "complete",
                    "--id",
                    measurement_id,
                    "--mixed-work",
                    mixed_work,
                )[1]
                self.assertEqual("low", completed["confidence"])
                self.assertIn(f"mixed_work_{mixed_work}", completed["anomalies"])

    def test_negative_efficiency_is_preserved(self) -> None:
        """AI 協作參考耗時高於基準時應保留負值。"""
        measurement_id = self.start()
        arguments: list[str] = []
        for phase in self.measure.PHASES:
            values = "10,10,10" if phase == "requirement_plan" else "0,0,0"
            arguments.extend(("--estimate", f"{phase}={values}"))
        code, _, _ = self.run_cli("baseline", "--id", measurement_id, *arguments)
        self.assertEqual(0, code)
        self.clock.advance(20)
        self.run_cli("pause", "--id", measurement_id)
        completed = self.run_cli(
            "complete",
            "--id",
            measurement_id,
            "--mixed-work",
            "no",
        )[1]
        self.assertEqual(-10, completed["saved_seconds"])
        self.assertEqual(-100.0, completed["efficiency_percent"])

    def test_baseline_fingerprint_mismatch_suppresses_efficiency(self) -> None:
        """基準指紋不一致時只保留耗時並揭露異常。"""
        measurement_id = self.start()
        self.lock_baseline(measurement_id)
        self.run_cli("pause", "--id", measurement_id)
        state_file = self.state_dir / f"{measurement_id}.json"
        state = self.measure.read_state(state_file)
        state["baseline"]["fingerprint"] = "invalid"
        self.measure.write_state(state_file, state)
        completed = self.run_cli(
            "complete",
            "--id",
            measurement_id,
            "--mixed-work",
            "no",
        )[1]
        self.assertNotIn("saved_seconds", completed)
        self.assertNotIn("efficiency_percent", completed)
        self.assertEqual("low", completed["confidence"])
        self.assertIn("baseline_fingerprint_mismatch", completed["anomalies"])

    def test_complete_is_idempotent_before_delete(self) -> None:
        """刪除前重複 complete 應回傳相同封存摘要。"""
        measurement_id = self.start()
        self.run_cli("pause", "--id", measurement_id)
        first = self.run_cli(
            "complete",
            "--id",
            measurement_id,
            "--mixed-work",
            "no",
        )[1]
        second = self.run_cli(
            "complete",
            "--id",
            measurement_id,
            "--mixed-work",
            "unknown",
        )[1]
        self.assertEqual(first, second)

    def test_activitywatch_uses_only_local_afk_gets_and_intersects_intervals(self) -> None:
        """ActivityWatch 只讀本機 AFK 事件並正確聚合交集。"""
        started_at = self.clock.value
        bucket_id = "aw-watcher-afk_test/host"
        requests, self.activitywatch_url = self.start_activitywatch_server(
            buckets={
                bucket_id: {
                    "id": bucket_id,
                    "type": "afkstatus",
                    "client": "aw-watcher-afk",
                    "hostname": socket.gethostname(),
                },
                "aw-watcher-window-test": {
                    "id": "aw-watcher-window-test",
                    "type": "currentwindow",
                    "client": "aw-watcher-window",
                    "hostname": socket.gethostname(),
                },
            },
            events=[
                {
                    "timestamp": self.measure.format_utc(started_at + 10),
                    "duration": 30,
                    "data": {"status": "not-afk"},
                },
                {
                    "timestamp": self.measure.format_utc(started_at + 20),
                    "duration": 30,
                    "data": {"status": "not-afk"},
                },
                {
                    "timestamp": self.measure.format_utc(started_at + 90),
                    "duration": 40,
                    "data": {"status": "not-afk"},
                },
                {
                    "timestamp": self.measure.format_utc(started_at + 50),
                    "duration": 40,
                    "data": {"status": "afk"},
                },
            ],
        )
        measurement_id = self.start(provider="activitywatch")
        self.clock.advance(100)
        self.run_cli("enter", "--id", measurement_id, "--phase", "test_design")
        self.clock.advance(100)
        self.run_cli("pause", "--id", measurement_id)
        completed = self.run_cli(
            "complete",
            "--id",
            measurement_id,
            "--mixed-work",
            "no",
        )[1]
        self.assertEqual("activitywatch", completed["source"])
        self.assertEqual(80, completed["seconds"])
        self.assertEqual(50, completed["phases"]["requirement_plan"])
        self.assertEqual(30, completed["phases"]["test_design"])
        self.assertTrue(all(method == "GET" for method, _ in requests))
        self.assertEqual(2, len(requests))
        event_path = requests[1][1]
        self.assertIn("/events?", event_path)
        self.assertIn("%2F", event_path)
        self.assertNotIn("window", unquote(event_path))
        parsed = urlsplit(event_path)
        self.assertIn("start=", parsed.query)
        self.assertIn("end=", parsed.query)

        state_file = self.state_dir / f"{measurement_id}.json"
        serialized = state_file.read_text(encoding="utf-8")
        for forbidden in (bucket_id, "not-afk", '"duration"', '"timestamp"'):
            self.assertNotIn(forbidden, serialized)

    def test_activitywatch_falls_back_for_ambiguous_bucket_and_server_error(self) -> None:
        """候選歧義與 API 錯誤都應降級為 session。"""
        local_metadata = {
            "type": "afkstatus",
            "client": "aw-watcher-afk",
            "hostname": socket.gethostname(),
        }
        cases = (
            ({"first": local_metadata, "second": local_metadata}, 200),
            ({}, 500),
        )
        for buckets, status in cases:
            with self.subTest(status=status, candidates=len(buckets)):
                requests, self.activitywatch_url = self.start_activitywatch_server(
                    buckets=buckets,
                    events=[],
                    buckets_status=status,
                )
                measurement_id = self.start(provider="activitywatch")
                self.clock.advance(20)
                self.run_cli("pause", "--id", measurement_id)
                completed = self.run_cli(
                    "complete",
                    "--id",
                    measurement_id,
                    "--mixed-work",
                    "no",
                )[1]
                self.assertEqual("session", completed["source"])
                self.assertEqual(20, completed["seconds"])
                self.assertEqual("low", completed["confidence"])
                self.assertIn("activitywatch_fallback", completed["anomalies"])
                self.assertEqual([("GET", "/api/0/buckets/")], requests)

    def test_activitywatch_rejects_non_loopback_and_external_redirect(self) -> None:
        """非 loopback 組態與外部導向都不得發出外部請求。"""
        for unsafe_url in (
            urlunsplit(("http", "user:secret@localhost:5600", "", "", "")),
            urlunsplit(("https", "localhost:5600", "", "", "")),
        ):
            with self.subTest(unsafe_url=unsafe_url):
                with self.assertRaises(self.measure.ActivityWatchError):
                    self.measure.validate_activitywatch_base_url(unsafe_url)
        self.activitywatch_url = "https://example.com:5600"
        measurement_id = self.start(provider="activitywatch")
        self.clock.advance(5)
        self.run_cli("pause", "--id", measurement_id)
        invalid_url_completed = self.run_cli(
            "complete",
            "--id",
            measurement_id,
            "--mixed-work",
            "no",
        )[1]
        self.assertEqual("session", invalid_url_completed["source"])
        self.assertIn("activitywatch_fallback", invalid_url_completed["anomalies"])

        requests, self.activitywatch_url = self.start_activitywatch_server(
            buckets={},
            events=[],
            redirect="https://example.com/activitywatch",
        )
        measurement_id = self.start(provider="activitywatch")
        self.clock.advance(5)
        self.run_cli("pause", "--id", measurement_id)
        redirected = self.run_cli(
            "complete",
            "--id",
            measurement_id,
            "--mixed-work",
            "no",
        )[1]
        self.assertEqual("session", redirected["source"])
        self.assertIn("activitywatch_fallback", redirected["anomalies"])
        self.assertEqual([("GET", "/api/0/buckets/")], requests)

    def test_activitywatch_timeout_falls_back_without_blocking_workflow(self) -> None:
        """ActivityWatch 逾時後應降級，不中斷完結流程。"""
        _, self.activitywatch_url = self.start_activitywatch_server(
            buckets={},
            events=[],
            delay=2.2,
        )
        measurement_id = self.start(provider="activitywatch")
        self.clock.advance(5)
        self.run_cli("pause", "--id", measurement_id)
        started = time.monotonic()
        completed = self.run_cli(
            "complete",
            "--id",
            measurement_id,
            "--mixed-work",
            "no",
        )[1]
        elapsed = time.monotonic() - started
        self.assertEqual("session", completed["source"])
        self.assertIn("activitywatch_fallback", completed["anomalies"])
        self.assertLess(elapsed, 2.2)


if __name__ == "__main__":
    unittest.main()
