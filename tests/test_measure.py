from __future__ import annotations

import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


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

    def run_cli(self, *arguments: str) -> tuple[int, dict[str, object], bytes]:
        """執行 CLI 並回傳 exit code、JSON 與原始輸出。"""
        output = io.StringIO()
        environment = {
            "AI_WORKFLOW_STATE_DIR": str(self.state_dir),
            "LOCALAPPDATA": self.temp_dir.name,
        }
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


if __name__ == "__main__":
    unittest.main()
