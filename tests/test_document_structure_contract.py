from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "ai-development-workflow"


class DocumentStructureContractTest(unittest.TestCase):
    """驗證需求計畫與測試設計的精簡、追溯與所有權合同。"""

    def read(self, relative: str) -> str:
        """讀取 Skill 內指定的 UTF-8 文件。"""
        return (SKILL_ROOT / relative).read_text(encoding="utf-8")

    def test_plan_uses_core_and_conditional_structure(self) -> None:
        """核心語義應保留，無證據的條件式區塊不應產生空表格。"""
        template = self.read("assets/requirement-plan-template.md")
        guide = self.read("references/requirement-plan.md")
        for expected in (
            "完整欄位目錄",
            "不是每份輸出都要逐章複製",
            "條件式",
            "否則刪除",
        ):
            self.assertIn(expected, template)
        self.assertIn("文件密度檔位", guide)
        self.assertIn("小型原生緊湊檔", guide)
        self.assertIn("只使用下列六個二級標題", guide)
        self.assertIn("不等於每項都必須擁有獨立標題", guide)
        self.assertIn("每個變更檔案獨立一列", guide)
        self.assertIn("至少兩位數零補齊", guide)
        self.assertIn("仍屬具體風險", guide)
        self.assertIn("只有存在對應證據時保留", guide)
        self.assertIn("2. **Provider 橋接**", guide)
        self.assertIn("13. **文件改動**", guide)

    def test_small_native_test_design_uses_compact_profile(self) -> None:
        """單一 seam、資料與命令的小型測試設計應合併標題。"""
        template = self.read("assets/test-design-template.md")
        guide = self.read("references/test-design.md")
        self.assertIn("完整欄位目錄", template)
        self.assertIn("小型原生緊湊檔", guide)
        self.assertIn("只保留下列五個二級標題", guide)
        self.assertIn("至少兩位數零補齊", guide)
        for expected in (
            "基本資訊與策略",
            "測試資料與情境",
            "自動化與執行",
            "回歸與交付",
            "實施結果與剩餘風險",
        ):
            self.assertIn(expected, guide)

    def test_framework_managed_test_seam_requires_minimal_preflight(self) -> None:
        """框架代理或載入期改寫類別應先驗證 runner 相容性與最小 seam。"""
        guide = self.read("references/test-design.md")
        for expected in (
            "runner 設定",
            "process isolation",
            "AOP",
            "代理生成",
            "alias／overload mock",
            "一個能證明 seam 可用的最小案例",
            "取得實作核准後",
        ):
            self.assertIn(expected, guide)
        self.assertIn("一般純函式", guide)
        self.assertIn("不為形式增加預檢表", guide)
        self.assertIn("測試設計階段不建立或執行測試程式碼", guide)

    def test_multiple_measurement_segments_use_compact_non_aggregated_summary(
        self,
    ) -> None:
        """多個有效計量分段應壓縮呈現但保留逐段證據與不可合併邊界。"""
        timing = self.read("references/reference-timing.md")
        template = self.read("assets/ai-collaboration-section-template.md")
        for expected in (
            "多分段摘要表",
            "分段／完整 ID",
            "不得以省略號、前後綴或短碼截斷",
            "獨立的計量模式與資料來源",
            "不得把模式／資料來源合併",
            "不得省略",
        ):
            self.assertIn(expected, timing)
        for expected in (
            "多分段摘要（條件式）",
            "參考計時指南的「完成後新增範圍」",
            "「回填與清理」",
            "| 範圍 | 計量模式與資料來源 |",
            "session｜ActivityWatch",
            "PERT 基準、鎖定／指紋",
            "AI 耗時／階段摘要",
            "覆蓋度／可信度",
            "異常／混入工作",
        ):
            self.assertIn(expected, template)

    def test_decision_and_delivery_statuses_are_independent(self) -> None:
        """文件核准與執行進度不得再共用一個含混狀態。"""
        plan = self.read("assets/requirement-plan-template.md")
        test_design = self.read("assets/test-design-template.md")
        plan_guide = self.read("references/requirement-plan.md")
        test_guide = self.read("references/test-design.md")
        for expected in ("計畫狀態", "交付狀態"):
            self.assertIn(expected, plan)
            self.assertIn(expected, plan_guide)
        for expected in ("設計狀態", "執行狀態"):
            self.assertIn(expected, test_design)
            self.assertIn(expected, test_guide)

    def test_plan_and_test_design_share_stable_traceability_ids(self) -> None:
        """驗收、切片、情境、資料與執行應以穩定 ID 串接。"""
        plan = self.read("assets/requirement-plan-template.md")
        test_design = self.read("assets/test-design-template.md")
        for expected in ("AC-01", "S-01", "T-01"):
            self.assertIn(expected, plan)
        for expected in ("AC-01", "T-01", "D-01", "RUN-01"):
            self.assertIn(expected, test_design)

    def test_test_design_uniquely_owns_commands_and_detailed_results(self) -> None:
        """需求計畫只保留驗證關卡，具體命令與逐情境結果由測試設計擁有。"""
        plan = self.read("assets/requirement-plan-template.md")
        test_design = self.read("assets/test-design-template.md")
        guide = self.read("references/requirement-plan.md")
        self.assertNotIn("指令或方式", plan)
        self.assertNotIn("可重現指令", plan)
        self.assertIn("具體命令由測試設計擁有", plan)
        self.assertIn("可重現命令或驗證方式", test_design)
        self.assertIn("詳細測試情境", guide)
        self.assertIn("只放在獨立 test-design", guide)

    def test_provider_bridge_is_compact_natively_but_preserves_external_ownership(self) -> None:
        """原生模式應精簡；外部正式產物仍保留完整橋接與所有權。"""
        plan = self.read("assets/requirement-plan-template.md")
        test_design = self.read("assets/test-design-template.md")
        guide = self.read("references/requirement-plan.md")
        integration = self.read("references/workflow-integration.md")
        for content in (plan, test_design):
            self.assertIn("原生模式", content)
            self.assertIn("外部 Provider 映射（條件式", content)
            self.assertIn("唯一可寫所有者", content)
        self.assertIn("只有存在活動外部產物時才展開橋接映射", guide)
        for expected in ("Matt Pocock Skills", "`to-spec`", "`to-tickets`"):
            self.assertIn(expected, integration)

    def test_ai_effectiveness_remains_separate_from_delivery_results(self) -> None:
        """AI 成效不得混入一般實作與驗證結果。"""
        template = self.read("assets/requirement-plan-template.md")
        guide = self.read("references/requirement-plan.md")
        self.assertNotIn("## AI 協作紀錄與成效", template)
        self.assertIn(
            "不是「實作與驗證結果」的一部分",
            guide,
        )
        self.assertIn("預設關閉", guide)

    def test_public_readmes_explain_compact_traceability_contract(self) -> None:
        """公開說明應同步緊湊檔位與穩定追蹤合同。"""
        traditional = (ROOT / "README.md").read_text(encoding="utf-8")
        english = (ROOT / "README.en.md").read_text(encoding="utf-8")
        self.assertIn("六個核心標題", traditional)
        self.assertIn("五個核心標題", traditional)
        self.assertIn("`AC-* → S-* → T-* → D-*／RUN-*`", traditional)
        self.assertIn("six core plan headings", english)
        self.assertIn("five core test-design headings", english)
        self.assertIn("`AC-* → S-* → T-* → D-* / RUN-*`", english)


if __name__ == "__main__":
    unittest.main()
