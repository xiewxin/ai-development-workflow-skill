import json
import shutil
import subprocess
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "ai-development-workflow"


def copy_skill_fixture(source: Path, destination: Path) -> None:
    """建立供發布驗證使用的獨立 Skill 夾具。"""
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


class PlanPackageContractTest(unittest.TestCase):
    """驗證新生成計畫包的身份、職責與執行交接合同。"""

    def read(self, relative: str) -> str:
        path = SKILL_ROOT / relative
        self.assertTrue(path.is_file(), f"缺少公開合同：{relative}")
        return path.read_text(encoding="utf-8")

    def read_json(self, relative: str) -> dict:
        return json.loads(self.read(relative))

    def test_publication_fixture_excludes_only_generated_bytecode(self) -> None:
        """測試產生的快取不得混入夾具；其他二進位檔仍須被發布檢查拒絕。"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / "source"
            shutil.copytree(SKILL_ROOT, source)
            cache = source / "scripts" / "__pycache__"
            cache.mkdir(exist_ok=True)
            (cache / "measure.cpython-312.pyc").write_bytes(b"\x00synthetic-bytecode")
            (source / "scripts" / "measure.pyc").write_bytes(b"\x00synthetic-bytecode")
            fixture = root / "clean-fixture"
            copy_skill_fixture(source, fixture)
            result = subprocess.run(
                ["bash", str(ROOT / "scripts/validate-publication.sh"), str(fixture)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout)

            (source / "scripts" / "unexpected.bin").write_bytes(b"\x00unexpected")
            rejected_fixture = root / "rejected-fixture"
            copy_skill_fixture(source, rejected_fixture)
            result = subprocess.run(
                ["bash", str(ROOT / "scripts/validate-publication.sh"), str(rejected_fixture)],
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("scripts/unexpected.bin", result.stdout)

    def test_skill_routes_new_plans_to_one_directory_package(self) -> None:
        skill = self.read("SKILL.md")
        contract = self.read("references/plan-package.md")
        for content in (skill, contract):
            self.assertIn("docs/plans/YYYY-MM-DD-<topic>/", content)
            for name in (
                "design.md",
                "delivery.md",
                "implementation.md",
                "test-design.md",
                "manifest.json",
                "execution.json",
            ):
                self.assertIn(name, content)
        self.assertIn("新生成內容只使用目錄式計畫包", contract)
        self.assertIn("不自動移動或刪除", contract)

    def test_artifacts_have_non_overlapping_ownership(self) -> None:
        contract = self.read("references/plan-package.md")
        design = self.read("assets/design-template.md")
        delivery = self.read("assets/delivery-template.md")
        implementation = self.read("assets/implementation-template.md")
        test_design = self.read("assets/test-design-template.md")
        for expected in ("單一職責", "唯一事實來源", "精確相對路徑"):
            self.assertIn(expected, contract)
        for expected in ("為什麼", "介面", "替代方案", "風險", "非目標"):
            self.assertIn(expected, design)
        for expected in ("目標", "範圍", "證據", "AC-01", "最終驗收"):
            self.assertIn(expected, delivery)
        for expected in ("測試矩陣", "邊界", "關鍵斷言", "RUN-01"):
            self.assertIn(expected, test_design)
        for link in ("./design.md", "./delivery.md", "./test-design.md"):
            self.assertIn(link, implementation)

    def test_implementation_is_directly_executable_by_superpowers(self) -> None:
        implementation = self.read("assets/implementation-template.md")
        for expected in (
            "superpowers:executing-plans",
            "superpowers:subagent-driven-development",
            "每個步驟約 2–5 分鐘",
            "**Interfaces:**",
            "**Dependencies:**",
            "AC-01",
            "S-01",
            "T-01",
            "Write the failing test",
            "Expected: FAIL",
            "Write minimal implementation",
            "Expected: PASS",
            "Review the task diff",
            "Run cumulative verification",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, implementation)
        self.assertNotIn("TBD", implementation)
        self.assertNotIn("TODO", implementation)

    def test_manifest_binds_approved_files_and_authorization_boundaries(self) -> None:
        manifest = self.read_json("assets/manifest-template.json")
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["plan_package_id"], "{{INPUT:plan-package-id}}")
        self.assertEqual(manifest["status"], "{{INPUT:draft|approved|superseded}}")
        self.assertEqual(
            set(manifest["files"]),
            {"design.md", "delivery.md", "implementation.md", "test-design.md"},
        )
        for metadata in manifest["files"].values():
            self.assertEqual(metadata["algorithm"], "sha256")
            self.assertEqual(metadata["sha256"], "{{INPUT:64-lowercase-hex}}")
        self.assertEqual(
            manifest["authorization"]["external_actions"],
            {
                "push": "separate_authorization",
                "pull_request": "separate_authorization",
                "merge": "separate_authorization",
                "release": "separate_authorization",
                "publish": "separate_authorization",
                "deploy": "separate_authorization",
                "remote_write": "separate_authorization",
                "api_mutation": "separate_authorization",
            },
        )
        for field in ("execution_mode", "worktree_policy", "commit_policy"):
            self.assertIn(field, manifest)

    def test_execution_owns_observed_runtime_state(self) -> None:
        execution = self.read_json("assets/execution-template.json")
        for field in ("plan_package_id", "manifest_sha256", "started_at", "finished_at"):
            self.assertIn(field, execution)
        task = execution["tasks"][0]
        for field in ("task_id", "status", "commands", "tests", "commit_sha"):
            self.assertIn(field, task)
        self.assertIn("actual", task["commands"][0])
        self.assertIn("exit_code", task["commands"][0])
        self.assertIn("actual", task["tests"][0])

        test_design = self.read("assets/test-design-template.md")
        delivery = self.read("assets/delivery-template.md")
        self.assertIn("## 執行證據索引", test_design)
        self.assertIn("execution.json", test_design)
        self.assertNotIn("## 自動化測試實施結果", test_design)
        self.assertNotIn("實際命令／結果", test_design)
        self.assertNotIn("| 結果 |", delivery)
        self.assertNotIn("交付狀態：", delivery)

    def test_approval_order_covers_optional_tasks_without_mutating_plan_facts(self) -> None:
        contract = self.read("references/plan-package.md")
        manifest = self.read_json("assets/manifest-template.json")
        for expected in (
            "先核准四份正式文件與執行策略",
            "再機械派生",
            "不需要第二次內容核准",
            "finalized_at",
            "finalized_at` 不是 `null`",
        ):
            self.assertIn(expected, contract)
        self.assertIn("finalized_at", manifest)
        self.assertIn("derived_tasks", manifest)

    def test_hashed_fact_corrections_and_test_design_precede_final_approval(self) -> None:
        requirement = self.read("references/requirement-plan.md")
        test_design = self.read("references/test-design.md")
        self.assertIn("已哈希的新計畫包", requirement)
        self.assertIn("事實更正也必須退回草擬", requirement)
        self.assertIn("整包最終核准前", test_design)
        self.assertNotIn("於需求計畫核准後、實作前建立", test_design)
        self.assertIn("已核准正式文件即使只是事實更正", self.read("SKILL.md"))

    def test_test_command_projection_has_one_canonical_owner(self) -> None:
        contract = self.read("references/plan-package.md")
        self.assertIn("驗證命令的唯一來源", contract)
        self.assertIn("機械摘錄", contract)
        self.assertIn("RUN-*", self.read("assets/implementation-template.md"))

    def test_handoff_has_external_approval_anchor_and_safe_materialization(self) -> None:
        contract = self.read("references/plan-package.md")
        for expected in (
            "外部核准紀錄", "approval_record", "新的 plan_package_id",
            "逐項驗證派生 Task", "符號連結", "目標已存在時停止",
            "發布檢查只驗證公開範本", "不得勾選正式文件",
        ):
            self.assertIn(expected, contract)

    def test_approval_binds_source_revision_and_single_execution_claim(self) -> None:
        manifest = self.read_json("assets/manifest-template.json")
        execution = self.read_json("assets/execution-template.json")
        for field in ("source_revision", "execution_id"):
            self.assertIn(field, manifest)
        self.assertIn("execution_id", execution)
        contract = self.read("references/plan-package.md")
        for expected in (
            "HEAD 必須等於 source_revision", "一次性執行收據", "superseded",
            "最新外部狀態", "不得重用", "預設回報目前對話",
            "tracker 寫入另需授權",
        ):
            self.assertIn(expected, contract)

    def test_task_briefs_carry_exact_global_constraints(self) -> None:
        implementation = self.read("assets/implementation-template.md")
        contract = self.read("references/plan-package.md")
        self.assertIn("**Required brief context:**", implementation)
        self.assertIn("exact values", implementation)
        self.assertIn("不得只交付 Task 摘錄", contract)

    def test_superpowers_bridge_checks_the_whole_capability_contract(self) -> None:
        contract = self.read("references/plan-package.md")
        implementation = self.read("assets/implementation-template.md")
        for expected in (
            "相容性矩陣", "current-checkout", "isolated-worktree",
            "task-local-commits", "ledger", "不合格", "materialization",
        ):
            self.assertIn(expected, contract)
        for expected in ("STOP", "reapproval", "manifest", "remote writes"):
            self.assertIn(expected, implementation)

    def test_cumulative_review_includes_committed_and_untracked_changes(self) -> None:
        execution = self.read_json("assets/execution-template.json")
        implementation = self.read("assets/implementation-template.md")
        self.assertIn("base_commit_sha", execution)
        self.assertIn("git diff {{INPUT:execution.base_commit_sha}}", implementation)
        self.assertIn("untracked", implementation)

    def test_publication_rejects_semantically_invalid_plan_package_templates(self) -> None:
        def derived_task(document: dict, **changes: str) -> None:
            document["files"]["implementation.md"]["sha256"] = "a" * 64
            document["derived_tasks"] = [{
                "task_id": "S-01", "path": "tasks/S-01.md",
                "sha256": "b" * 64, "parent_implementation_sha256": "a" * 64,
                **changes,
            }]

        mutations = (
            ("manifest", lambda d: d.update(unrecognized_permission=True)),
            ("manifest", lambda d: d["files"]["design.md"].update(extra="unsupported")),
            ("manifest", lambda d: d.update(source_revision="wrong-base")),
            ("manifest", lambda d: d.update(execution_mode="surprise")),
            ("manifest", lambda d: d.update(worktree_policy="any-directory")),
            ("manifest", lambda d: d.update(commit_policy="push-everything")),
            ("manifest", lambda d: d.update(schema_version=True)),
            ("manifest", lambda d: d["files"]["design.md"].update(sha256="fake")),
            ("manifest", lambda d: d.pop("approval_record", None)),
            ("manifest", lambda d: d.update(derived_tasks={})),
            ("manifest", lambda d: derived_task(d, path="tasks/../../escape.md")),
            ("manifest", lambda d: derived_task(d, path="/tasks/S-01.md")),
            ("manifest", lambda d: derived_task(d, sha256="fake")),
            ("manifest", lambda d: derived_task(d, parent_implementation_sha256="c" * 64)),
            ("manifest", lambda d: d["authorization"]["external_actions"].pop("remote_write", None)),
            ("execution", lambda d: d["tasks"][0]["commands"][0].pop("recorded_at")),
            ("execution", lambda d: d["tasks"][0]["tests"][0].pop("evidence")),
            ("execution", lambda d: d["tasks"][0].update(commit_sha="not-a-sha")),
            ("execution", lambda d: d.update(status="made_up")),
            ("execution", lambda d: d.update(unrecognized_result=True)),
            ("execution", lambda d: d.update(status="completed")),
            ("execution", lambda d: d["tasks"][0].update(status="completed")),
            ("execution", lambda d: d["tasks"][0]["commands"][0].update(extra="unsupported")),
            ("execution", lambda d: d["tasks"][0]["commands"].append(dict(d["tasks"][0]["commands"][0]))),
            ("execution", lambda d: d.update(cumulative_verification=[dict(d["tasks"][0]["commands"][0])])),
            ("execution", lambda d: d["tasks"][0]["tests"][0].update(run_id="RUN-99")),
        )
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary).resolve() / "skill"
            copy_skill_fixture(SKILL_ROOT, fixture)
            baseline = subprocess.run(
                ["bash", str(ROOT / "scripts/validate-publication.sh"), str(fixture)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(baseline.returncode, 0, baseline.stdout)
            manifest_path = fixture / "assets" / "manifest-template.json"
            original_manifest = manifest_path.read_text(encoding="utf-8")
            valid_task_manifest = json.loads(original_manifest)
            derived_task(valid_task_manifest)
            manifest_path.write_text(json.dumps(valid_task_manifest), encoding="utf-8")
            valid_task_result = subprocess.run(
                ["bash", str(ROOT / "scripts/validate-publication.sh"), str(fixture)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(valid_task_result.returncode, 0, valid_task_result.stdout)
            manifest_path.write_text(original_manifest, encoding="utf-8")
            for kind, mutate in mutations:
                with self.subTest(kind=kind, mutation=mutate.__code__.co_firstlineno):
                    path = fixture / "assets" / f"{kind}-template.json"
                    original = path.read_text(encoding="utf-8")
                    payload = json.loads(original)
                    mutate(payload)
                    path.write_text(json.dumps(payload), encoding="utf-8")
                    result = subprocess.run(
                        ["bash", str(ROOT / "scripts/validate-publication.sh"), str(fixture)],
                        capture_output=True, text=True, check=False,
                    )
                    path.write_text(original, encoding="utf-8")
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    self.assertIn(f"[{kind} 欄位]", result.stdout)

    def test_publication_accepts_complete_execution_evidence(self) -> None:
        manifest = self.read_json("assets/manifest-template.json")
        manifest.update(
            plan_package_id="example-plan", execution_id="example-execution",
            source_revision="a" * 40, status="approved",
            approved_at="2026-01-01T00:00:00Z", finalized_at="2026-01-01T00:01:00Z",
            approval_record="example-conversation", execution_mode="inline",
            worktree_policy="isolated-worktree", commit_policy="none",
        )
        for metadata in manifest["files"].values():
            metadata["sha256"] = "b" * 64
        execution = self.read_json("assets/execution-template.json")
        execution.update(
            plan_package_id="example-plan", execution_id="example-execution",
            manifest_sha256="c" * 64, base_commit_sha="a" * 40,
            status="completed", started_at="2026-01-01T00:02:00Z",
            finished_at="2026-01-01T00:04:00Z", worktree="worktrees/example",
            final_diff_review="passed",
        )
        command = {
            "run_id": "RUN-01", "planned_run_id": "RUN-01", "workdir": ".", "actual": "test-command",
            "recorded_at": "2026-01-01T00:03:00Z", "exit_code": 0, "result": "passed",
        }
        execution["tasks"][0].update(
            status="completed", changed_files=["src/example.py"], diff_review="passed",
            commands=[command], tests=[{
                "test_id": "T-01", "run_id": "RUN-01", "actual": "passed",
                "recorded_at": "2026-01-01T00:03:00Z", "evidence": "example-output",
                "status": "passed",
            }],
        )
        execution["cumulative_verification"] = [{**command, "run_id": "RUN-02"}]
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary).resolve() / "skill"
            copy_skill_fixture(SKILL_ROOT, fixture)
            for kind, payload in (("manifest", manifest), ("execution", execution)):
                (fixture / "assets" / f"{kind}-template.json").write_text(
                    json.dumps(payload), encoding="utf-8",
                )
            result = subprocess.run(
                ["bash", str(ROOT / "scripts/validate-publication.sh"), str(fixture)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout)

            manifest["commit_policy"] = "task-local-commits"
            execution["final_commit_sha"] = None
            (fixture / "assets" / "manifest-template.json").write_text(
                json.dumps(manifest), encoding="utf-8",
            )
            (fixture / "assets" / "execution-template.json").write_text(
                json.dumps(execution), encoding="utf-8",
            )
            result = subprocess.run(
                ["bash", str(ROOT / "scripts/validate-publication.sh"), str(fixture)],
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("[execution 欄位]", result.stdout)
            execution["tasks"][0]["commit_sha"] = "e" * 40
            (fixture / "assets" / "execution-template.json").write_text(
                json.dumps(execution), encoding="utf-8",
            )
            result = subprocess.run(
                ["bash", str(ROOT / "scripts/validate-publication.sh"), str(fixture)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            execution["tasks"][0]["commit_sha"] = None
            (fixture / "assets" / "execution-template.json").write_text(
                json.dumps(execution), encoding="utf-8",
            )
            manifest["commit_policy"] = "final-local-commit"
            (fixture / "assets" / "manifest-template.json").write_text(
                json.dumps(manifest), encoding="utf-8",
            )
            result = subprocess.run(
                ["bash", str(ROOT / "scripts/validate-publication.sh"), str(fixture)],
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("[execution 欄位]", result.stdout)
            execution["final_commit_sha"] = "d" * 40
            (fixture / "assets" / "execution-template.json").write_text(
                json.dumps(execution), encoding="utf-8",
            )
            result = subprocess.run(
                ["bash", str(ROOT / "scripts/validate-publication.sh"), str(fixture)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout)

    def test_completed_execution_retains_history_without_masking_latest_failure(self) -> None:
        """重試可保留失敗歷史；不同驗證與後來失敗不能被成功觀測掩蓋。"""
        manifest = self.read_json("assets/manifest-template.json")
        manifest.update(
            plan_package_id="retry-plan", execution_id="retry-execution",
            source_revision="a" * 40, status="approved",
            approved_at="2026-01-01T00:00:00Z", finalized_at="2026-01-01T00:01:00Z",
            approval_record="example-conversation", execution_mode="inline",
            worktree_policy="isolated-worktree", commit_policy="none",
        )
        for metadata in manifest["files"].values():
            metadata["sha256"] = "b" * 64
        execution = self.read_json("assets/execution-template.json")
        execution.update(
            plan_package_id="retry-plan", execution_id="retry-execution",
            manifest_sha256="c" * 64, base_commit_sha="a" * 40,
            status="completed", started_at="2026-01-01T00:02:00Z",
            finished_at="2026-01-01T00:04:00Z", worktree="worktrees/example",
            final_diff_review="passed",
        )
        command = {"run_id": "RUN-01", "planned_run_id": "RUN-01", "workdir": ".",
                   "actual": "test-command", "recorded_at": "2026-01-01T00:03:00Z",
                   "exit_code": 1, "result": "expected RED"}
        green = {**command, "run_id": "RUN-02", "exit_code": 0, "result": "passed"}
        test = {"test_id": "T-01", "run_id": "RUN-01", "actual": "test-command",
                "recorded_at": command["recorded_at"], "evidence": "red-output", "status": "failed"}
        passed = {**test, "run_id": "RUN-02", "evidence": "green-output", "status": "passed"}
        execution["tasks"][0].update(status="completed", changed_files=["src/example.py"],
                                      commands=[command, green], tests=[passed], diff_review="passed")
        failed_full = {**command, "run_id": "RUN-09", "planned_run_id": "RUN-10", "actual": "full-check", "result": "failed"}
        passed_full = {**failed_full, "run_id": "RUN-04", "exit_code": 0, "result": "passed"}
        cases = (
            ("cumulative retry", [passed], [failed_full, passed_full], True),
            ("RED and GREEN tests", [test, passed], [passed_full], True),
            ("latest test failed", [passed, test], [passed_full], False),
            ("different test succeeded", [test, {**passed, "test_id": "T-02"}], [passed_full], False),
            ("latest cumulative failed", [passed], [passed_full, failed_full], False),
            ("different planned check", [passed], [failed_full, {**passed_full, "planned_run_id": "RUN-11"}], False),
            ("different working directory", [passed], [failed_full, {**passed_full, "workdir": "other"}], False),
            ("unplanned exact retry", [passed], [{**failed_full, "planned_run_id": None}, {**passed_full, "planned_run_id": None}], True),
            ("unplanned unrelated success", [passed], [{**failed_full, "planned_run_id": None}, {**passed_full, "planned_run_id": None, "actual": "unrelated-check"}], False),
        )
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary).resolve() / "skill"
            copy_skill_fixture(SKILL_ROOT, fixture)
            (fixture / "assets/manifest-template.json").write_text(json.dumps(manifest), encoding="utf-8")
            for name, tests, cumulative, accepted in cases:
                with self.subTest(case=name):
                    execution["tasks"][0]["tests"] = tests
                    execution["cumulative_verification"] = cumulative
                    (fixture / "assets/execution-template.json").write_text(json.dumps(execution), encoding="utf-8")
                    result = subprocess.run(
                        ["bash", str(ROOT / "scripts/validate-publication.sh"), str(fixture)],
                        capture_output=True, text=True, check=False,
                    )
                    if accepted:
                        self.assertEqual(result.returncode, 0, result.stdout)
                    else:
                        self.assertNotEqual(result.returncode, 0, result.stdout)
                        self.assertIn("[execution 欄位]", result.stdout)

    def test_each_remote_receipt_write_requires_separate_authorization(self) -> None:
        contract = self.read("references/plan-package.md")
        self.assertIn("每一次 tracker／API 狀態寫入", contract)
        self.assertIn("動作前", contract)
        self.assertIn("最初核准不能打包涵蓋", contract)

    def test_optional_tasks_are_derived_and_bound_to_parent(self) -> None:
        contract = self.read("references/plan-package.md")
        task_template = self.read("assets/task-template.md")
        for reason in ("並行", "跨會話", "跨倉庫", "高風險隔離"):
            self.assertIn(reason, contract)
        self.assertIn("預設不生成 `tasks/`", contract)
        for expected in (
            "父計畫路徑",
            "父計畫 SHA-256",
            "Task ID",
            "AC-*",
            "依賴",
            "Allowed files",
            "派生執行包",
            "不是第二份事實來源",
        ):
            self.assertIn(expected, task_template)

    def test_materialization_revalidates_identity_without_copying_extra_files(self) -> None:
        contract = self.read("references/plan-package.md")
        for expected in (
            "相同相對路徑",
            "複製前",
            "複製後",
            "重新計算 SHA-256",
            "不得複製秘密",
            "未核准文件",
            "驗證失敗時停止",
        ):
            self.assertIn(expected, contract)

    def test_process_artifacts_remain_git_ignored(self) -> None:
        guide = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        contract = self.read("references/plan-package.md")
        self.assertIn("docs/plans/", guide)
        self.assertIn("must not be committed", guide)
        self.assertIn("docs/plans/", contract)
        self.assertIn("不得提交", contract)
        self.assertIn("docs/plans/*", ignore)

    def test_public_docs_and_examples_explain_the_plan_package(self) -> None:
        traditional = (ROOT / "README.md").read_text(encoding="utf-8")
        english = (ROOT / "README.en.md").read_text(encoding="utf-8")
        examples = self.read("references/examples.md")
        for expected in (
            "docs/plans/YYYY-MM-DD-<topic>/",
            "implementation.md",
            "manifest.json",
            "execution.json",
        ):
            self.assertIn(expected, traditional)
            self.assertIn(expected, english)
            self.assertIn(expected, examples)
        self.assertIn("Superpowers", traditional)
        self.assertIn("Superpowers", english)
        self.assertIn("SHA-256", examples)

    def test_provider_bridge_consumes_the_neutral_execution_contract_directly(self) -> None:
        integration = self.read("references/workflow-integration.md")
        for expected in (
            "`implementation.md`",
            "不需要格式轉換",
            "`manifest.json`",
            "`execution.json`",
            "不得把本 Skill 變成程式碼執行器",
        ):
            self.assertIn(expected, integration)

    def test_scenarios_cover_worktree_materialization_and_separate_authorization(self) -> None:
        scenarios = (ROOT / "tests" / "scenarios.md").read_text(encoding="utf-8")
        self.assertIn("情境二十八：核准計畫包交給隔離 worktree 執行", scenarios)
        for expected in (
            "相同相對路徑",
            "重新計算 SHA-256",
            "execution_mode",
            "worktree_policy",
            "commit_policy",
            "push、PR、merge、release、publish",
        ):
            self.assertIn(expected, scenarios)


if __name__ == "__main__":
    unittest.main()
