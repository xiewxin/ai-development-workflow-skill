from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "ai-development-workflow"


class OpenSourceDefaultsContractTest(unittest.TestCase):
    """驗證 AI 成效 opt-in 與自適應語言策略。"""

    def read(self, relative: str) -> str:
        """讀取 Skill 內指定的 UTF-8 文件。"""
        return (SKILL_ROOT / relative).read_text(encoding="utf-8")

    def test_default_plan_omits_ai_collaboration_section(self) -> None:
        """未明確啟用時，基本需求計畫不得產生 AI 成效章節。"""
        template = self.read("assets/requirement-plan-template.md")
        self.assertNotIn("## AI 協作紀錄與成效", template)
        self.assertNotIn("AI 協作參考耗時", template)

    def test_optional_ai_section_preserves_complete_measurement_contract(
        self,
    ) -> None:
        """明確 opt-in 時仍可套用完整且可驗證的既有欄位。"""
        optional = self.read("assets/ai-collaboration-section-template.md")
        for expected in (
            "## AI 協作紀錄與成效",
            "../references/reference-timing.md",
            "### 可驗證貢獻",
            "### 效率量化",
            "計量 ID",
            "計量覆蓋度",
            "人工參考基準與鎖定時間",
            "AI 協作參考耗時",
            "參考提效比例",
            "歸因限制",
            "狀態清理結果",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, optional)

    def test_language_policy_separates_interaction_and_repository_artifacts(
        self,
    ) -> None:
        """互動跟隨使用者，檔案與程式碼跟隨目標 repo。"""
        skill = self.read("SKILL.md")
        self.assertIn("## 語言選擇規則", skill)
        self.assertIn("互動語言跟隨使用者", skill)
        self.assertIn("目標倉庫規範", skill)
        self.assertIn("附近檔案慣例", skill)
        self.assertIn("固定合同／識別字保持原文", skill)
        self.assertNotIn("所有說明、計畫、測試設計與審查結論預設使用繁體中文", skill)

    def test_timing_and_ai_section_are_disabled_by_default(self) -> None:
        """沒有明確需求或 repo 政策時不得啟動計時。"""
        skill = self.read("SKILL.md")
        guide = self.read("references/requirement-plan.md")
        timing = self.read("references/reference-timing.md")
        for content in (skill, guide, timing):
            self.assertIn("預設關閉", content)
            self.assertIn("使用者明確要求", content)
        self.assertNotIn("完整流程預設啟用", timing)

    def test_timing_uses_complete_coverage_and_never_calculates_tokens(self) -> None:
        """時間提效只接受完整覆蓋，且不得收集或估算 Token。"""
        skill = self.read("SKILL.md")
        timing = self.read("references/reference-timing.md")
        template = self.read("assets/ai-collaboration-section-template.md")
        for content in (skill, timing, template):
            self.assertIn("不收集", content)
            self.assertIn("Token", content)
        self.assertIn("--coverage complete", timing)
        self.assertIn("續接回合的第一個計時動作", timing)
        self.assertIn("等待使用者、CI 或外部佇列前", timing)
        self.assertIn("計量覆蓋度", template)

    def test_test_design_uses_repository_language_policy(self) -> None:
        """測試設計語言需跟隨互動與 repo，不固定繁體。"""
        guide = self.read("references/test-design.md")
        self.assertIn("互動語言", guide)
        self.assertIn("目標倉庫", guide)
        self.assertNotIn("預設使用繁體中文", guide)


if __name__ == "__main__":
    unittest.main()
