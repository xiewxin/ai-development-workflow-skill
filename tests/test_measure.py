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


if __name__ == "__main__":
    unittest.main()
