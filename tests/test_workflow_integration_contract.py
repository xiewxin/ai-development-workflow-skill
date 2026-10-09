from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "ai-development-workflow"


class WorkflowIntegrationContractTest(unittest.TestCase):
    """驗證外部工作流能力適配與橋接合同。"""

    def read(self, relative: str) -> str:
        """讀取 Skill 內指定的 UTF-8 文件。"""
        return (SKILL_ROOT / relative).read_text(encoding="utf-8")

    def test_provider_reference_only_defines_constraints_and_profiles(self) -> None:
        """Provider reference 應只保留產物、安全與已知 profile 約束。"""
        integration = self.read("references/workflow-integration.md")
        for expected in (
            "Provider 約束檔案",
            "## 啟用邊界",
            "## 共用產物與所有權約束",
            "## Provider profiles",
            "## 命令與副作用約束",
            "## 橋接與同步",
            "Superpowers",
            "Matt Pocock Skills",
            "Spec Kit",
            "OpenSpec",
            "BMAD",
            "未知工作流",
        ):
            self.assertIn(expected, integration)
        self.assertNotIn("## 主 Provider 選擇", integration)
        self.assertIn("不得創造可用性", integration)
        self.assertIn("提高品牌排序", integration)

    def test_bridge_schema_is_present_in_both_templates(self) -> None:
        """需求與測試範本應共用最小 Provider 橋接欄位。"""
        requirement = self.read("assets/requirement-plan-template.md")
        test_design = self.read("assets/test-design-template.md")
        requirement_guide = self.read("references/requirement-plan.md")
        for text in (requirement, test_design):
            self.assertIn("Provider 橋接", text)
            for expected in (
                "需求級工作流所有者",
                "階段能力執行者",
                "產物定位",
                "唯一可寫所有者",
                "完整性",
                "同步結果",
            ):
                self.assertIn(expected, text)
        self.assertIn("能力／階段能力執行者", requirement_guide)
        self.assertNotIn("能力、Provider、產物定位", requirement_guide)
        self.assertIn("測試優先級", test_design)
        self.assertNotIn("能力／階段能力執行者／優先級", test_design)

    def test_integration_forbids_implicit_mutating_commands(self) -> None:
        """整合不得隱式執行具外部副作用的命令。"""
        integration = self.read("references/workflow-integration.md")
        orchestration = self.read("references/skill-orchestration.md")
        for expected in (
            "不得自動安裝",
            "不自動 setup",
            "不假裝自動調用",
        ):
            self.assertIn(expected, orchestration + integration)

    def test_review_sources_converge_to_one_rev_list(self) -> None:
        """多個審查來源應收斂為單一 REV 問題清單。"""
        review = self.read("references/git-diff-review.md")
        self.assertIn("多來源審查", review)
        self.assertIn("REV-*", review)
        self.assertIn("去重", review)

    def test_workflow_owner_and_stage_executor_are_distinct_roles(self) -> None:
        """需求級工作流所有者與階段執行者不得混為同一角色。"""
        integration = self.read("references/workflow-integration.md")
        orchestration = self.read("references/skill-orchestration.md")
        requirement = self.read("references/requirement-plan.md")
        self.assertIn("需求級工作流所有者", orchestration)
        self.assertIn("階段能力執行者", orchestration)
        self.assertIn("每份正式產物只有一個唯一可寫所有者", orchestration)
        self.assertIn("不因入選取得其他階段或正式產物的所有權", integration)
        self.assertIn("只對有明確正式產物的能力擁有內容", requirement)

    def test_unknown_provider_has_explicit_write_boundary(self) -> None:
        """未知 Provider 所有權不明時不得猜測寫入。"""
        integration = self.read("references/workflow-integration.md")
        self.assertIn("所有權不明時不得寫入該產物", integration)
        self.assertIn("必要正式交付", integration)
        self.assertIn("阻斷受影響階段", integration)
        self.assertIn("非必要產物則標記為唯讀證據", integration)
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
            "User-invoked",
            "Model-invoked",
            "不自動 setup",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, integration)
        self.assertIn("平台本輪提供的 Skill catalog metadata", skill)
        self.assertIn("不因已安裝、已載入或品牌名稱建立候選", skill)
        self.assertIn("計畫已可直接執行時不預設拆票", integration)

    def test_provider_profiles_cannot_create_or_rank_candidates(self) -> None:
        """已知 Provider profile 不能取代平台 catalog 或通用排序。"""
        integration = self.read("references/workflow-integration.md")
        for expected in (
            "已出現在階段能力快照",
            "不得創造可用性",
            "提高品牌排序",
            "觸發安裝",
            "未知 Provider 不需要先加入本文件",
        ):
            self.assertIn(expected, integration)

    def test_cross_provider_composition_requires_non_overlap_or_handoff(self) -> None:
        """跨 Provider 只能分槽或按最小產物交接合同安全串接。"""
        orchestration = self.read("references/skill-orchestration.md")
        integration = self.read("references/workflow-integration.md")
        for expected in (
            "## 跨 Provider 能力組合",
            "互不重疊的能力槽",
            "明確的上游／下游關係",
            "同一能力槽、寫入範圍或正式產物",
            "只保留一個主執行者",
            "能力包不可拆分",
            "唯讀第二來源",
            "可驗證的獨立增益",
            "產物交接合同",
            "穩定定位、唯一所有者與新鮮度",
            "精確能力與唯讀輸入邊界",
            "獨立輸出及其唯一可寫所有者",
            "禁止回寫上游",
            "返回驗證與原生替代",
            "跨任務恢復或版本可能混淆",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, orchestration)
        for expected in (
            "Superpowers 與 Matt",
            "不能同時擁有實作執行槽",
            "TDD 槽只選一個主執行者",
            "審查只作唯讀第二來源",
            "產物交接合同",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, integration)

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
