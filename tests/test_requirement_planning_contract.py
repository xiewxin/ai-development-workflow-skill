from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "ai-development-workflow"


class RequirementPlanningContractTest(unittest.TestCase):
    """驗證需求計畫的適應性細化與可執行切片合同。"""

    def read(self, relative: str) -> str:
        """讀取 Skill 內指定的 UTF-8 文件。"""
        return (SKILL_ROOT / relative).read_text(encoding="utf-8")

    def test_clarification_resolves_facts_before_asking_decisions(self) -> None:
        """可查事實應自行探索，必要決策才逐題確認。"""
        guide = self.read("references/requirement-plan.md")
        for expected in (
            "可由環境查證的事實",
            "一次只問一個問題",
            "建議答案",
            "不重複提問",
        ):
            self.assertIn(expected, guide)

    def test_plan_template_uses_adaptive_behavior_scenarios(self) -> None:
        """只有適用時才展開使用者可觀察行為。"""
        skill = self.read("SKILL.md")
        guide = self.read("references/requirement-plan.md")
        template = self.read("assets/requirement-plan-template.md")
        self.assertIn("可觀察行為場景", skill)
        self.assertIn("適應性細化", guide)
        self.assertIn("行為與驗收場景（僅適用時保留）", template)
        self.assertIn("不強制產生冗長 User Stories", guide)

    def test_plan_selects_a_high_stable_test_seam(self) -> None:
        """計畫需以使用者可觀察的最高穩定公開介面為測試 seam。"""
        skill = self.read("SKILL.md")
        guide = self.read("references/requirement-plan.md")
        template = self.read("assets/requirement-plan-template.md")
        for content in (skill, guide, template):
            self.assertIn("測試 seam", content)
            self.assertIn("使用者可觀察", content)
        self.assertIn("現成低層測試不能充分驗證可見合同", guide)

    def test_implementation_uses_vertical_slices_and_blocking_edges(self) -> None:
        """實作切片應表達端到端成果、阻塞關係與完成判準。"""
        guide = self.read("references/requirement-plan.md")
        template = self.read("assets/requirement-plan-template.md")
        for expected in (
            "## 實作切片",
            "端到端可驗證成果",
            "Blocked by",
            "完成判準",
        ):
            self.assertIn(expected, template)
        self.assertIn("垂直切片", guide)
        self.assertIn("阻塞關係", guide)

    def test_wide_refactor_uses_expand_migrate_contract(self) -> None:
        """無法垂直切分的廣泛機械變更應維持可回歸遷移。"""
        guide = self.read("references/requirement-plan.md")
        for expected in (
            "Wide refactor",
            "expand → migrate → contract",
            "整合關卡",
        ):
            self.assertIn(expected, guide)


if __name__ == "__main__":
    unittest.main()
