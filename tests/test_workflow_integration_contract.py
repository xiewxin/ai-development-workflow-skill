from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "ai-development-workflow"


class WorkflowIntegrationContractTest(unittest.TestCase):
    """驗證外部工作流能力適配與橋接合同。"""

    def read(self, relative: str) -> str:
        """讀取 Skill 內指定的 UTF-8 文件。"""
        return (SKILL_ROOT / relative).read_text(encoding="utf-8")

    def test_provider_reference_defines_selection_and_fallback(self) -> None:
        """Provider reference 應完整定義選擇、所有權與降級。"""
        integration = self.read("references/workflow-integration.md")
        for expected in (
            "## 能力合同",
            "## 主 Provider 選擇",
            "## 多倉庫所有權",
            "## Provider Profile",
            "## 命令安全與授權",
            "## 降級規則",
            "Superpowers",
            "Matt Pocock Skills",
            "Spec Kit",
            "OpenSpec",
            "BMAD",
            "未知工作流",
            "可選 Provider",
            "強制 Provider",
        ):
            self.assertIn(expected, integration)

    def test_bridge_schema_is_present_in_both_templates(self) -> None:
        """需求與測試範本應共用最小 Provider 橋接欄位。"""
        requirement = self.read("assets/requirement-plan-template.md")
        test_design = self.read("assets/test-design-template.md")
        for text in (requirement, test_design):
            self.assertIn("Provider 橋接", text)
            for expected in (
                "主 Provider",
                "產物定位",
                "唯一可寫所有者",
                "完整性",
                "同步結果",
            ):
                self.assertIn(expected, text)

    def test_integration_forbids_implicit_mutating_commands(self) -> None:
        """整合不得隱式執行具外部副作用的命令。"""
        integration = self.read("references/workflow-integration.md")
        for expected in (
            "不自動安裝",
            "不自動初始化",
            "不自動封存",
            "不自動發布",
        ):
            self.assertIn(expected, integration)

    def test_review_sources_converge_to_one_rev_list(self) -> None:
        """多個審查來源應收斂為單一 REV 問題清單。"""
        review = self.read("references/git-diff-review.md")
        self.assertIn("多來源審查", review)
        self.assertIn("REV-*", review)
        self.assertIn("去重", review)

    def test_main_provider_and_content_owner_are_distinct_roles(self) -> None:
        """主 Provider 沒有正式產物時應指定能力級內容所有者。"""
        integration = self.read("references/workflow-integration.md")
        requirement = self.read("references/requirement-plan.md")
        self.assertIn("主 Provider 不等於每個產物的內容所有者", integration)
        self.assertIn("本 Skill 成為該能力的唯一可寫所有者", integration)
        self.assertIn("不改變需求級主 Provider", integration)
        self.assertIn("只對有明確正式產物的能力擁有內容", requirement)

    def test_unknown_provider_has_explicit_write_boundary(self) -> None:
        """未知 Provider 所有權不明時不得猜測寫入。"""
        integration = self.read("references/workflow-integration.md")
        self.assertIn("所有權不明時不得寫入該產物", integration)
        self.assertIn("必要正式交付", integration)
        self.assertIn("阻斷受影響階段", integration)
        self.assertIn("非必要產物", integration)
        self.assertIn("同步未驗證", integration)

    def test_matt_pocock_provider_maps_artifacts_and_side_effects(self) -> None:
        """Matt Provider 應區分釐清、正式產物與實作副作用。"""
        skill = self.read("SKILL.md")
        integration = self.read("references/workflow-integration.md")
        for expected in (
            "### Matt Pocock Skills",
            "`grill-with-docs`",
            "`to-spec`",
            "`to-tickets`",
            "`wayfinder`",
            "`tdd`",
            "`code-review`",
            "`implement`",
            "tracker 識別字",
            "提交授權",
            "已安裝不代表",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, integration)
        self.assertIn("目前對話已明確觸發或使用", integration)
        self.assertNotIn("平台目前已載入且可用的 Skill 或能力清單", integration)
        self.assertIn("只有名稱、可用能力清單、已安裝工具或目錄存在不構成啟用證據", skill)

    def test_bridge_schema_accepts_tracker_artifact_identifiers(self) -> None:
        """外部正式產物不在 repo 時應可使用穩定 tracker 識別字。"""
        requirement = self.read("assets/requirement-plan-template.md")
        test_design = self.read("assets/test-design-template.md")
        guide = self.read("references/requirement-plan.md")
        for content in (requirement, test_design, guide):
            self.assertIn("tracker 識別字", content)
        self.assertIn("相對路徑或 tracker 識別字", guide)


if __name__ == "__main__":
    unittest.main()
