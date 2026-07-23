from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RepositoryGuidanceContractTest(unittest.TestCase):
    """驗證公開倉庫維護指南維持精簡、可導航且具明確邊界。"""

    def read(self, relative: str) -> str:
        """讀取倉庫內指定的 UTF-8 文件。"""
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_root_guide_is_concise_and_indexes_detail(self) -> None:
        """根指南應保留穩定規則，並直接索引需要的子文件。"""
        guide = self.read("AGENTS.md")
        self.assertLessEqual(len(guide.splitlines()), 80)
        for expected in (
            "## Sources of truth",
            "## Maintainer guide index",
            "## Runtime boundary",
            "## Editing rules",
            "## Verification",
            "## Release boundary",
            ".agents/adr/0001-runtime-boundary.md",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, guide)

    def test_process_artifacts_and_public_sources_stay_separate(self) -> None:
        """維護指南不得把本機計畫提升成公開功能來源。"""
        guide = self.read("AGENTS.md")
        self.assertIn("docs/plans/", guide)
        self.assertIn("docs/specs/", guide)
        self.assertIn("ignored process artifacts", guide)
        self.assertIn("must not be committed", guide)

    def test_runtime_decision_preserves_optional_timing(self) -> None:
        """ADR 應鎖定 Markdown 核心與可降級的 Python 計時邊界。"""
        decision = self.read(".agents/adr/0001-runtime-boundary.md")
        for expected in (
            "Keep the public Skill Markdown-first",
            "Keep `measure.py` standard-library-only and optional",
            "Do not require Python for the core workflow",
            "Missing Python is an explicit timing fallback",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, decision)


if __name__ == "__main__":
    unittest.main()
