from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "ai-development-workflow"


class ReviewContractTest(unittest.TestCase):
    """驗證審查問題與計畫同步的公開合同。"""

    def read(self, relative: str) -> str:
        """讀取 Skill 內指定的 UTF-8 文件。"""
        return (SKILL_ROOT / relative).read_text(encoding="utf-8")

    def test_review_uses_stable_ids_and_three_severities(self) -> None:
        """審查問題應使用穩定編號、三檔嚴重度與完整狀態。"""
        review = self.read("references/git-diff-review.md")
        for expected in (
            "## 嚴重度",
            "## Finding 合同",
            "## 問題狀態",
            "## 複審輸出",
            "REV-001",
            "高",
            "中",
            "低",
            "緊急",
            "待處理",
            "已修正待驗證",
            "已關閉",
            "接受風險",
        ):
            self.assertIn(expected, review)
        for legacy in ("**P0**", "**P1**", "**P2**", "**P3**"):
            self.assertNotIn(legacy, review)

    def test_test_priority_remains_p0_to_p3(self) -> None:
        """測試情境仍應保留風險導向的 P0 至 P3 排序。"""
        test_design = self.read("references/test-design.md")
        for priority in ("P0", "P1", "P2", "P3"):
            self.assertIn(priority, test_design)

    def test_plan_change_sync_is_explicit(self) -> None:
        """計畫應區分事實更正、候選變更與已核准偏差。"""
        guide = self.read("references/requirement-plan.md")
        template = self.read("assets/requirement-plan-template.md")
        for expected in ("待核准候選變更", "事實更正", "已核准偏差", "退回草擬"):
            self.assertIn(expected, guide)
        self.assertIn("## 變更紀錄", template)
        for expected in ("候選", "核准證據", "同步結果"):
            self.assertIn(expected, template)


if __name__ == "__main__":
    unittest.main()
