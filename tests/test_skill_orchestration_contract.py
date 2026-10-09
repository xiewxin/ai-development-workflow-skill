from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "ai-development-workflow"


class SkillOrchestrationContractTest(unittest.TestCase):
    """驗證平台中立、可退出且可安全降級的 Skill 編排合同。"""

    def read(self, relative: str) -> str:
        """讀取 Skill 內指定的 UTF-8 文件，並將缺檔視為合同失敗。"""
        path = SKILL_ROOT / relative
        self.assertTrue(path.is_file(), f"缺少公開合同：{relative}")
        return path.read_text(encoding="utf-8")

    def assert_all_in(self, content: str, expected: tuple[str, ...]) -> None:
        """逐項驗證必要合同文字存在，保留明確的失敗項目。"""
        for item in expected:
            with self.subTest(expected=item):
                self.assertIn(item, content)

    def test_reference_exists_and_skill_routes_to_it(self) -> None:
        """通用編排 reference 應存在，並由公開 Skill 按需導航。"""
        orchestration = self.read("references/skill-orchestration.md")
        skill = self.read("SKILL.md")
        self.assertIn("# Skill 編排合同", orchestration)
        self.assertIn("references/skill-orchestration.md", skill)

    def test_catalog_is_the_only_discovery_source(self) -> None:
        """能力發現只接受平台本輪 catalog，不掃描或安裝本機 Skill。"""
        orchestration = self.read("references/skill-orchestration.md")
        self.assert_all_in(
            orchestration,
            (
                "發現不等於啟用",
                "平台本輪提供的 Skill catalog metadata",
                "不得掃描全部本機 Skill",
                "不得自動安裝",
                "Provider 約束檔案不得創造可用性",
                "品牌或 Skill 名稱本身不足",
            ),
        )

    def test_dual_inputs_fast_paths_and_lifecycle_are_explicit(self) -> None:
        """雙入口需分流，零／一／多快速路徑與實際生命週期不得混寫。"""
        skill = self.read("SKILL.md")
        orchestration = self.read("references/skill-orchestration.md")
        self.assert_all_in(
            skill,
            (
                "主動發現入口",
                "顯式調用上下文",
                "不重新發現或排名",
                "| 待核驗能力 | 處理 |",
                "| 0 |",
                "| 1 |",
                "| 多個 |",
            ),
        )
        self.assert_all_in(
            orchestration,
            (
                "## 雙入口與候選快速路徑",
                "不掃描本機",
                "不補造 `selected`",
                "不再次 `invoked`",
                "`observed → qualified → selected`",
                "`invoked → returned → consumed`",
                "`handoff_pending → returned → consumed`",
                "只展開目前最高優先組",
                "唯一合格候選",
                "不做虛假比較",
                "`native_fallback`",
                "`blocked`",
            ),
        )

    def test_trigger_boundary_phases_and_slots_are_stable(self) -> None:
        """窄觸發邊界、六個編排階段與核心能力槽應明確分離。"""
        orchestration = self.read("references/skill-orchestration.md")
        self.assert_all_in(
            orchestration,
            (
                "使用者入口模式",
                "明確要求跨 Skill 開發交付協調",
                "不攔截",
                "需求計畫",
                "測試設計",
                "實作",
                "驗證與修復",
                "文件同步",
                "Git Diff 審查",
                "核心能力槽",
                "catalog 不得動態擴張",
            ),
        )

    def test_candidates_require_two_stage_verification_and_hard_gates(self) -> None:
        """metadata 初篩後仍須核驗完整合同及排序前硬門檻。"""
        orchestration = self.read("references/skill-orchestration.md")
        skill = self.read("SKILL.md")
        self.assert_all_in(
            orchestration,
            (
                "metadata 初篩",
                "待核驗短名單",
                "不直接建立候選",
                "完整候選合同",
                "最高優先組",
                "同組候選",
                "使用者明確選擇與活動正式產物延續",
                "一般競爭組",
                "不以 metadata 描述粒度預先拆組",
                "不得因某候選先被讀取",
                "任務內復用",
                "失效條件",
                "強制合同",
                "可用性",
                "調用模式",
                "授權",
                "副作用",
                "產物所有權",
                "選用優先序",
                "同級決勝",
                "最低交接成本",
            ),
        )
        self.assertIn("metadata 只能預篩", skill)
        self.assertIn("先按需讀取編排 reference", skill)
        self.assertIn("最高優先組決勝", skill)

    def test_ownership_slots_and_bundles_do_not_overlap(self) -> None:
        """需求級所有者、槽執行者與不可拆能力包應有唯一寫入邊界。"""
        orchestration = self.read("references/skill-orchestration.md")
        self.assert_all_in(
            orchestration,
            (
                "需求級工作流所有者",
                "階段能力執行者",
                "每個能力槽只有一個主執行者",
                "正式產物",
                "唯一可寫所有者",
                "能力包",
                "全有或全無",
            ),
        )

    def test_invocation_modes_dependencies_and_handoff_are_explicit(self) -> None:
        """Model-invoked 可觸發；User-invoked 只能單動作交接並暫停。"""
        orchestration = self.read("references/skill-orchestration.md")
        self.assert_all_in(
            orchestration,
            (
                "Model-invoked",
                "User-invoked",
                "顯式調用指示",
                "一項目前動作",
                "暫停",
                "調用依賴鏈",
                "不完整依賴",
                "不自動 setup",
                "恢復條件",
                "原生替代",
            ),
        )
        self.assertNotIn("第三方命令大全", orchestration)

    def test_tickets_are_conditional_derived_execution_artifacts(self) -> None:
        """計畫完成不預設拆票，派生 tickets 不反向取得計畫維護權。"""
        orchestration = self.read("references/skill-orchestration.md")
        self.assert_all_in(
            orchestration,
            (
                "不預設調用 `to-tickets`",
                "長期追蹤",
                "複雜協作",
                "外部 tracker",
                "派生執行工作清單",
                "唯讀上游輸入",
                "不取得上游計畫的設計維護權",
                "必要 ID 映射",
            ),
        )

    def test_handoffs_and_persistence_are_minimal(self) -> None:
        """同任務交接不落盤，跨任務只保存必要恢復狀態。"""
        orchestration = self.read("references/skill-orchestration.md")
        self.assert_all_in(
            orchestration,
            (
                "同一任務",
                "跨任務",
                "緊湊交接卡",
                "最小交接狀態",
                "重新驗證實際產物",
                "不保存",
                "排名",
                "合同快取",
                "調用統計",
            ),
        )

    def test_result_acceptance_pass_does_not_imply_consumption(self) -> None:
        """結果接納判定通過只允許使用，未實際使用仍停在 returned。"""
        orchestration = self.read("references/skill-orchestration.md")
        scenarios = (ROOT / "tests" / "scenarios.md").read_text(encoding="utf-8")
        self.assert_all_in(
            orchestration,
            (
                "### 結果接納判定",
                "同一任務",
                "不落盤",
                "唯一關聯",
                "目前用途",
                "判定通過只允許下游使用",
                "實際使用前仍保持 `returned`",
            ),
        )
        self.assertIn("`ORCH-035`", scenarios)
        self.assertIn("判定通過但沒有實際用於下游產物或決策", scenarios)
        self.assertIn("生命週期保持 `returned`", scenarios)

    def test_consumption_requires_material_downstream_effect(self) -> None:
        """採納與否不是 consumed 判準，實質影響下游才是。"""
        orchestration = self.read("references/skill-orchestration.md")
        scenarios = (ROOT / "tests" / "scenarios.md").read_text(encoding="utf-8")
        self.assert_all_in(
            orchestration,
            (
                "實質影響下游產物或決策",
                "採納、拒絕或暫緩",
                "僅接收、轉述、展示或存檔",
                "不得標記 `consumed`",
            ),
        )
        self.assertIn("`ORCH-036`", scenarios)
        self.assertIn("改變下游決策", scenarios)
        self.assertIn("採納、拒絕或暫緩", scenarios)
        self.assertIn("標記 `consumed`", scenarios)

    def test_result_acceptance_invalidation_and_failure_routing_are_bounded(
        self,
    ) -> None:
        """用途改變只重判適配；安全漂移或不確定性需完整核驗。"""
        orchestration = self.read("references/skill-orchestration.md")
        scenarios = (ROOT / "tests" / "scenarios.md").read_text(encoding="utf-8")
        self.assert_all_in(
            orchestration,
            (
                "下游用途改變",
                "只重新判定用途適配",
                "能力身份或版本",
                "授權、工作樹、產物所有權或實際副作用",
                "無法判定的漂移",
                "完整候選合同核驗",
                "缺失、不完整或不適配",
                "`native_fallback`",
                "授權、身份、安全、所有權或強制合同",
                "`blocked`",
                "一則緊湊提示",
                "已觀察副作用",
                "原生接續",
                "一項必要決策",
                "被要求或執行正式評估",
            ),
        )
        self.assertIn("`ORCH-037`", scenarios)
        self.assertIn("普通內容問題", scenarios)
        self.assertIn("安全或所有權衝突", scenarios)
        self.assertIn("原生回退", scenarios)
        self.assertIn("`blocked`", scenarios)

    def test_result_acceptance_has_one_behavior_owner(self) -> None:
        """規則只由編排 reference 擁有，其他公開文件不得複製算法。"""
        context = (ROOT / "CONTEXT.md").read_text(encoding="utf-8")
        self.assertIn("**結果接納判定**", context)
        self.assertIn(
            "skills/ai-development-workflow/references/skill-orchestration.md"
            "#結果接納判定",
            context,
        )
        self.assertIn(
            "skills/ai-development-workflow/references/skill-orchestration.md"
            "#能力執行生命週期",
            context,
        )
        for algorithm_fragment in (
            "結果可唯一關聯到目前調用",
            "下游用途改變只重判適配",
            "能力身份／版本、授權、工作樹",
            "無法判定的漂移",
            "內容實質影響下游產物或決策",
            "採納、拒絕或暫緩建議",
            "僅接收、轉述、展示或存檔",
        ):
            with self.subTest(context_algorithm=algorithm_fragment):
                self.assertNotIn(algorithm_fragment, context)
        for relative in ("SKILL.md", "references/workflow-integration.md"):
            with self.subTest(relative=relative):
                self.assertNotIn("結果接納判定", self.read(relative))
        for path in (ROOT / "README.md", ROOT / "README.en.md"):
            with self.subTest(path=path.name):
                self.assertNotIn("結果接納判定", path.read_text(encoding="utf-8"))

    def test_user_concern_gate_avoids_plan_bloat(self) -> None:
        """只有使用者需行動或恢復時才可見，不新增常駐計畫結構。"""
        orchestration = self.read("references/skill-orchestration.md")
        self.assert_all_in(
            orchestration,
            (
                "使用者關切門檻",
                "執行動作",
                "額外授權",
                "裁決正式產物衝突",
                "跨任務恢復",
                "不需要關心",
                "不得為保存這些資訊新增常駐計畫章節或預設欄位",
            ),
        )

    def test_direct_path_native_fallback_and_safe_degradation_are_complete(
        self,
    ) -> None:
        """無安全增益時走原生路徑，失效後依實際副作用安全接續。"""
        orchestration = self.read("references/skill-orchestration.md")
        self.assert_all_in(
            orchestration,
            (
                "直接路徑",
                "原生回退",
                "可驗證增益",
                "安全降級",
                "部分成果",
                "所有權不明",
                "遠端副作用",
                "不得盲目重跑",
                "REV-*",
                "審查收斂",
            ),
        )

    def test_validation_states_keep_contract_behavior_and_provider_scope_separate(
        self,
    ) -> None:
        """公開合同、真實行為與具名 Provider 結論不得互相冒充。"""
        orchestration = self.read("references/skill-orchestration.md")
        self.assert_all_in(
            orchestration,
            (
                "## 編排驗證合同",
                "`passed`",
                "`failed`",
                "`not_observed`",
                "`insufficient_evidence`",
                "運行時不可用",
                "`blocked` 是生命週期狀態",
                "公開確定性合同",
                "不能單獨證明真實行為或效率",
                "一項 Model-invoked 能力到達 `consumed`",
                "一項 User-invoked 交接返回並到達 `consumed`",
                "一次 `native_fallback`",
                "具名 Provider 能力分開彙總",
                "`failed → insufficient_evidence → not_observed → passed`",
                "不得安裝、掃描或以合成能力補成通過",
            ),
        )

    def test_provider_reference_only_constrains_active_capability_inputs(self) -> None:
        """Provider 文件只能收緊候選或顯式上下文，不創造能力與品牌排序。"""
        integration = self.read("references/workflow-integration.md")
        self.assert_all_in(
            integration,
            (
                "Provider 約束檔案",
                "已出現在階段能力快照",
                "目前任務已成立的顯式調用上下文",
                "不得創造可用性",
                "較保守",
            ),
        )
        self.assertNotIn("## 主 Provider 選擇", integration)

    def test_all_orchestration_scenarios_use_fictional_catalog_inputs(self) -> None:
        """ORCH 行為矩陣應完整且不依賴維護者本機安裝狀態。"""
        scenarios = (ROOT / "tests" / "scenarios.md").read_text(encoding="utf-8")
        for index in range(1, 38):
            with self.subTest(scenario=index):
                self.assertIn(f"`ORCH-{index:03d}`", scenarios)
        self.assertIn("全部為虛構測試資料", scenarios)
        self.assertIn("不依賴維護者本機安裝狀態", scenarios)
        self.assertIn("不執行第三方命令或遠端寫入", scenarios)

    def test_public_readmes_explain_dynamic_handoff_and_native_fallback(
        self,
    ) -> None:
        """中英文 README 應說明 catalog、單動作交接與使用者關切門檻。"""
        traditional = (ROOT / "README.md").read_text(encoding="utf-8")
        english = (ROOT / "README.en.md").read_text(encoding="utf-8")
        for expected in (
            "平台本輪提供的 Skill catalog metadata",
            "發現不等於啟用",
            "一項目前平台可執行的顯式調用指示",
            "不預設產生 tickets",
            "只有使用者需要行動",
            "不會自動安裝、setup、初始化、提交",
        ):
            with self.subTest(language="zh", expected=expected):
                self.assertIn(expected, traditional)
        for expected in (
            "Discovery is not activation",
            "one currently executable handoff action",
            "not sent to a ticket generator by default",
            "only when the user must act",
            "never installs, sets up, initializes, commits",
        ):
            with self.subTest(language="en", expected=expected):
                self.assertIn(expected, english)

    def test_public_metadata_describes_full_delivery_and_coordination(self) -> None:
        """公開入口應涵蓋實作與協調，但不把具名 Provider 寫成預設。"""
        traditional = (ROOT / "README.md").read_text(encoding="utf-8")
        english = (ROOT / "README.en.md").read_text(encoding="utf-8")
        metadata = self.read("agents/openai.yaml")
        self.assert_all_in(
            traditional,
            (
                "顯式調用上下文",
                "待核驗能力為零／一／多項",
                "metadata 初篩不直接建立候選",
                "跨 Provider 能力組合",
                "產物交接合同",
            ),
        )
        self.assert_all_in(
            english,
            (
                "explicit invocation context",
                "zero, one, or multiple capabilities pending verification",
                "Metadata filtering does not itself create a candidate",
                "cross-provider composition",
                "artifact handoff contract",
            ),
        )
        self.assertIn("端到端實作", metadata)
        self.assertIn("跨 Skill 協調", metadata)
        short_description = next(
            line.split('"', 2)[1]
            for line in metadata.splitlines()
            if line.strip().startswith("short_description:")
        )
        self.assertGreaterEqual(len(short_description), 25)
        self.assertLessEqual(len(short_description), 64)
        self.assertNotIn("Matt", short_description)
        self.assertNotIn("Superpowers", short_description)


if __name__ == "__main__":
    unittest.main()
