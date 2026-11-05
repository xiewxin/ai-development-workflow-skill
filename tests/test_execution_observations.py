"""Exercise execution identity, command/test consistency and manual evidence."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/ai-development-workflow"
BASH_EXECUTABLE = shutil.which("bash") or "bash"


class ExecutionObservationTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.skill = Path(self.temporary.name).resolve() / "skill"
        shutil.copytree(SKILL, self.skill, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        self.manifest = json.loads((SKILL / "assets/manifest-template.json").read_text())
        self.manifest.update(plan_package_id="observation-plan", execution_id="observation-execution",
                             source_revision="a" * 40, status="approved", approved_at="2026-01-01T00:00:00Z",
                             finalized_at="2026-01-01T00:01:00Z", approval_record="test-conversation",
                             execution_mode="inline", worktree_policy="isolated-worktree", commit_policy="none")
        for metadata in self.manifest["files"].values():
            metadata["sha256"] = "b" * 64
        self.execution = json.loads((SKILL / "assets/execution-template.json").read_text())
        self.execution.update(plan_package_id="observation-plan", execution_id="observation-execution",
                              manifest_sha256="c" * 64, base_commit_sha="a" * 40, status="completed",
                              started_at="2026-01-01T00:02:00Z", finished_at="2026-01-01T00:04:00Z",
                              worktree="worktrees/example", final_diff_review="passed")
        self.command = dict(run_id="RUN-01", planned_run_id="RUN-01", workdir=".", actual="test-command",
                            recorded_at="2026-01-01T00:03:00Z", exit_code=0, result="passed")
        self.test = dict(test_id="T-01", run_id="RUN-01", actual="test-command",
                         recorded_at=self.command["recorded_at"], evidence="test-output", status="passed")
        self.execution["tasks"][0].update(status="completed", changed_files=["src/example.py"],
                                          diff_review="passed", commands=[self.command], tests=[self.test])
        self.execution["cumulative_verification"] = [{**self.command, "run_id": "RUN-03"}]

    def validate(self, execution, accepted, error_kind="execution"):
        for name, value in (("manifest", self.manifest), ("execution", execution)):
            (self.skill / f"assets/{name}-template.json").write_text(json.dumps(value))
        result = subprocess.run([BASH_EXECUTABLE, str(ROOT / "scripts/validate-publication.sh"), str(self.skill)],
                                capture_output=True, encoding="utf-8", check=False)
        self.assertEqual(result.returncode, 0 if accepted else 1, result.stdout + result.stderr)
        if not accepted:
            self.assertIn(f"[{error_kind} 欄位]", result.stdout)

    def test_passed_test_requires_its_own_successful_command(self):
        self.validate(self.execution, True)
        failed = copy.deepcopy(self.execution)
        failed["tasks"][0]["commands"] = [
            {**self.command, "exit_code": 1, "result": "expected RED"},
            {**self.command, "run_id": "RUN-02", "planned_run_id": None, "actual": "git status"},
        ]
        self.validate(failed, False)
        # Keep legitimate RED history and bind the passed test to actual GREEN.
        retry = copy.deepcopy(failed)
        retry["tasks"][0]["commands"][1].update(actual="test-command", planned_run_id="RUN-01")
        retry["tasks"][0]["tests"][0]["run_id"] = "RUN-02"
        self.validate(retry, True)

    def test_passed_test_cannot_borrow_another_tasks_command(self):
        second = copy.deepcopy(self.execution["tasks"][0])
        second.update(task_id="S-02", commands=[{**self.command, "run_id": "RUN-02"}])
        self.execution["tasks"].append(second)  # T-01 still points to S-01's RUN-01.
        self.validate(self.execution, False)

    def manual_execution(self):
        manual = copy.deepcopy(self.execution)
        observation = {**self.command, "kind": "manual", "actual": "Inspect field labels in browser",
                       "exit_code": None, "result": "passed", "evidence": "evidence/field-labels.png"}
        manual["tasks"][0]["commands"] = [observation]
        manual["tasks"][0]["tests"][0].update(actual=observation["actual"], evidence=observation["evidence"])
        manual["cumulative_verification"] = [{**observation, "run_id": "RUN-03"}]
        return manual

    def test_manual_checks_complete_without_fabricated_exit_codes(self):
        self.validate(self.manual_execution(), True)

    def test_manual_checks_reject_missing_evidence_failure_or_fake_exit_code(self):
        for field, value in (("evidence", ""), ("result", "failed"), ("exit_code", 0), ("kind", "unknown")):
            with self.subTest(field=field):
                manual = self.manual_execution()
                manual["tasks"][0]["commands"][0][field] = value
                self.validate(manual, False)
        for field, value in (("evidence", ""), ("result", "failed"), ("exit_code", 0)):
            with self.subTest(cumulative_field=field):
                manual = self.manual_execution()
                manual["cumulative_verification"][0][field] = value
                self.validate(manual, False)

    def test_automatic_checks_cannot_drop_exit_code(self):
        self.execution["tasks"][0]["commands"][0]["exit_code"] = None
        self.validate(self.execution, False)

    def test_mixed_verification_does_not_mask_failed_automation(self):
        mixed = self.manual_execution()
        manual = mixed["tasks"][0]["commands"][0]
        manual["run_id"] = "RUN-02"
        manual_test = mixed["tasks"][0]["tests"][0]
        manual_test.update(test_id="T-02", run_id="RUN-02")
        mixed["tasks"][0]["commands"].insert(0, self.command)
        mixed["tasks"][0]["tests"].insert(0, self.test)
        mixed["cumulative_verification"] = [
            {**self.command, "run_id": "RUN-03"}, {**manual, "run_id": "RUN-04", "planned_run_id": "RUN-02"},
        ]
        self.validate(mixed, True)
        mixed["tasks"][0]["commands"][0]["exit_code"] = 1
        self.validate(mixed, False)

    def test_pending_manual_observation_is_not_completed_evidence(self):
        pending = self.manual_execution()
        pending.update(status="in_progress", finished_at=None, final_diff_review="not_run", cumulative_verification=[])
        task = pending["tasks"][0]
        task.update(status="in_progress", diff_review="not_run")
        task["commands"][0].update(actual=None, recorded_at=None, evidence=None, result="not_run")
        task["tests"][0].update(actual=None, recorded_at=None, evidence=None, status="not_run")
        self.validate(pending, True)
        pending.update(status="completed", finished_at="2026-01-01T00:04:00Z", final_diff_review="passed")
        task.update(status="completed", diff_review="passed")
        self.validate(pending, False)

    def test_cumulative_manual_success_cannot_replace_failed_automation(self):
        mixed = self.manual_execution()
        manual = mixed["cumulative_verification"][0]
        failed = {**self.command, "run_id": "RUN-04", "exit_code": 1, "result": "failed"}
        # Even the same planned RUN must retain both verification methods.
        mixed["cumulative_verification"] = [failed, manual]
        self.validate(mixed, False)
        mixed["cumulative_verification"] = [manual, failed]
        self.validate(mixed, False)
        # A real successful rerun of the command resolves its own failure.
        mixed["cumulative_verification"].append({**self.command, "run_id": "RUN-05"})
        self.validate(mixed, True)

    def test_started_execution_requires_finalized_manifest(self):
        original = copy.deepcopy(self.manifest)
        for status in ("in_progress", "partial", "completed", "blocked", "superseded"):
            for changes in (
                {"status": "draft", "approved_at": None, "finalized_at": None},
                {"finalized_at": None},
                {"finalized_at": "{{INPUT:ISO-8601-or-null}}"},
            ):
                with self.subTest(status=status, changes=changes):
                    self.manifest = {**original, **changes}
                    execution = {**self.execution, "status": status}
                    self.validate(execution, False)

    def test_started_execution_rejects_unresolved_bindings(self):
        original = copy.deepcopy(self.manifest)
        cases = (
            ("execution", "manifest_sha256", "{{INPUT:64-lowercase-hex}}"),
            ("shared", "plan_package_id", "{{INPUT:plan-package-id}}"),
            ("shared", "execution_id", "{{INPUT:single-execution-id}}"),
            ("manifest", "approval_record", "{{INPUT:user-visible-conversation-or-tracker-identifier}}"),
            ("manifest", "execution_mode", "{{INPUT:inline|executing-plans|subagent-driven-development|provider}}"),
            ("manifest", "worktree_policy", "{{INPUT:current-checkout|isolated-worktree}}"),
            ("manifest", "commit_policy", "{{INPUT:none|task-local-commits|final-local-commit}}"),
            ("file", "design.md", "{{INPUT:64-lowercase-hex}}"),
            ("contract", "contracts/api.md", "{{INPUT:64-lowercase-hex}}"),
        )
        for kind, field, value in cases:
            with self.subTest(kind=kind, field=field):
                self.manifest = copy.deepcopy(original)
                execution = copy.deepcopy(self.execution)
                if kind in ("execution", "shared"):
                    execution[field] = value
                if kind in ("manifest", "shared"):
                    self.manifest[field] = value
                if kind == "file":
                    self.manifest["files"][field]["sha256"] = value
                if kind == "contract":
                    self.manifest["contract_files"] = {field: {"algorithm": "sha256", "sha256": value}}
                self.validate(execution, False)

    def test_not_started_template_allows_unresolved_inputs(self):
        self.manifest = json.loads((SKILL / "assets/manifest-template.json").read_text())
        execution = json.loads((SKILL / "assets/execution-template.json").read_text())
        self.validate(execution, True)
        # Approval can precede finalization without claiming execution started.
        self.manifest.update(status="approved", approved_at="2026-01-01T00:00:00Z", finalized_at=None)
        self.validate(execution, True)

    def test_finalized_started_states_remain_valid(self):
        for status in ("in_progress", "partial", "completed", "blocked", "superseded"):
            with self.subTest(status=status):
                self.validate({**self.execution, "status": status}, True)

    def test_finalized_superseded_history_remains_readable(self):
        self.manifest["status"] = "superseded"
        for status in ("completed", "superseded"):
            with self.subTest(status=status):
                self.validate({**self.execution, "status": status}, True)

    def pending_execution(self, root_status="in_progress", kind="command"):
        execution = copy.deepcopy(self.execution)
        execution.update(status=root_status, finished_at=None, final_diff_review="not_run",
                         cumulative_verification=[])
        if root_status == "not_started":
            execution.update(started_at=None, base_commit_sha=None)
        command = {**self.command, "actual": None, "recorded_at": None,
                   "exit_code": None, "result": "not_run"}
        if kind == "manual":
            command.update(kind="manual", evidence=None)
        test = {**self.test, "actual": None, "recorded_at": None, "evidence": None, "status": "not_run"}
        execution["tasks"][0].update(status="not_started", changed_files=[], diff_review="not_run",
                                      commit_sha=None, commands=[command], tests=[test])
        return execution

    def test_not_started_execution_rejects_observed_collections(self):
        self.manifest.update(status="draft", approved_at=None, finalized_at=None)
        self.validate(self.pending_execution("not_started"), True)
        for kind in ("command", "manual"):
            with self.subTest(pending_kind=kind):
                pending = self.pending_execution("not_started", kind)
                planned = {**pending["tasks"][0]["commands"][0], "run_id": "RUN-03"}
                pending["cumulative_verification"] = [planned]
                self.validate(pending, True)
        for collection in ("command", "manual", "test_failed", "test_blocked", "test_skipped",
                           "cumulative_command", "cumulative_manual"):
            with self.subTest(collection=collection):
                execution = self.pending_execution("not_started")
                task = execution["tasks"][0]
                if collection == "command":
                    task["commands"] = [self.command]
                elif collection == "manual":
                    task["commands"] = self.manual_execution()["tasks"][0]["commands"]
                elif collection.startswith("test_"):
                    task["tests"] = [{**self.test, "status": collection.removeprefix("test_")}]
                elif collection == "cumulative_command":
                    execution["cumulative_verification"] = self.execution["cumulative_verification"]
                else:
                    execution["cumulative_verification"] = self.manual_execution()["cumulative_verification"]
                self.validate(execution, False)

    def test_task_state_observation_matrix(self):
        # Literal contract expectations: pending observations / real observations.
        states = (
            ("not_started", True, False), ("in_progress", True, True),
            ("partial", True, True), ("completed", False, True),
            ("blocked", True, True), ("superseded", True, True),
        )
        for status, pending_allowed, observed_allowed in states:
            for kind in ("command", "manual"):
                for observed, accepted in ((False, pending_allowed), (True, observed_allowed)):
                    with self.subTest(status=status, kind=kind, observed=observed):
                        execution = self.pending_execution(kind=kind)
                        task = execution["tasks"][0]
                        task["status"] = status
                        if observed:
                            source = self.manual_execution() if kind == "manual" else self.execution
                            task.update(commands=source["tasks"][0]["commands"], tests=source["tasks"][0]["tests"])
                        if status == "completed":
                            task.update(diff_review="passed", changed_files=["src/example.py"])
                        self.validate(execution, accepted)

    def test_not_started_task_rejects_test_results_without_command_observation(self):
        for status in ("failed", "blocked", "skipped"):
            with self.subTest(status=status):
                execution = self.pending_execution()
                execution["tasks"][0]["tests"] = [{**self.test, "status": status}]
                self.validate(execution, False)

    def test_not_started_metadata_cannot_claim_completed_work(self):
        for root_status in ("not_started", "in_progress"):
            for field, value in (("changed_files", ["src/example.py"]), ("diff_review", "passed"),
                                 ("diff_review", "failed"), ("diff_review", "blocked"), ("commit_sha", "d" * 40)):
                with self.subTest(root_status=root_status, task_field=field, value=value):
                    self.manifest["commit_policy"] = "task-local-commits"
                    execution = self.pending_execution(root_status)
                    execution["tasks"][0][field] = value
                    self.validate(execution, False)
        self.manifest["commit_policy"] = "final-local-commit"
        for field, value in (("base_commit_sha", "a" * 40), ("final_commit_sha", "d" * 40),
                             ("final_diff_review", "passed"), ("final_diff_review", "failed"),
                             ("final_diff_review", "blocked")):
            with self.subTest(execution_field=field, value=value):
                execution = self.pending_execution("not_started")
                execution[field] = value
                self.validate(execution, False)

    def test_workdir_observation_matrix(self):
        for kind in ("command", "manual"):
            for collection in ("task", "cumulative"):
                for result, placeholder_allowed in (("not_run", True), ("passed", False),
                                                    ("failed", False), ("blocked", False)):
                    for workdir, accepted in ((".", True), ("tests/fixtures", True),
                                              ("{{INPUT:repository-relative-path}}", placeholder_allowed),
                                              ("", False), ("/outside", False), ("../outside", False)):
                        with self.subTest(kind=kind, collection=collection, result=result, workdir=workdir):
                            execution = self.pending_execution(kind=kind)
                            execution["tasks"][0]["status"] = "in_progress"
                            record = copy.deepcopy(execution["tasks"][0]["commands"][0])
                            record.update(workdir=workdir, result=result)
                            if result != "not_run":
                                record.update(actual="Inspect output", recorded_at=self.command["recorded_at"],
                                              exit_code=0 if result == "passed" else 1)
                                if kind == "manual":
                                    record.update(exit_code=None, evidence="evidence/checklist.md")
                            if collection == "task":
                                execution["tasks"][0]["commands"] = [record]
                            else:
                                record["run_id"] = "RUN-03"
                                execution["cumulative_verification"] = [record]
                            self.validate(execution, accepted)

    def test_worktree_identity_lifecycle_matrix(self):
        states = (("not_started", True), ("in_progress", False), ("partial", False),
                  ("completed", False), ("blocked", False), ("superseded", False))
        for policy in ("current-checkout", "isolated-worktree"):
            self.manifest["worktree_policy"] = policy
            for status, unresolved_allowed in states:
                for identity, accepted in ((None, unresolved_allowed),
                                            ("{{INPUT:repository-relative-identity-or-null}}", unresolved_allowed),
                                            (".", True), ("worktrees/example", True)):
                    with self.subTest(policy=policy, status=status, identity=identity):
                        execution = self.pending_execution("not_started") if status == "not_started" else copy.deepcopy(self.execution)
                        execution.update(status=status, worktree=identity)
                        self.validate(execution, accepted)

    def test_approval_finalization_time_order_before_execution(self):
        cases = (
            ("2026-01-01T00:00:00Z", "2026-01-01T00:01:00Z", True),
            ("2026-01-01T00:00:00Z", "2025-12-31T23:59:59Z", False),
            ("2026-01-01T08:00:00+08:00", "2026-01-01T00:00:00Z", True),
            ("2026-01-01T00:00:00Z", "2026-01-01T08:00:00+09:00", False),
            ("2026-01-01T00:00:00Z", "2025-12-31T23:00:00-01:00", True),
        )
        for approved, finalized, accepted in cases:
            with self.subTest(approved=approved, finalized=finalized):
                self.manifest.update(approved_at=approved, finalized_at=finalized)
                self.validate(self.pending_execution("not_started"), accepted, "manifest")

    def test_started_lifecycle_time_order(self):
        original = copy.deepcopy(self.manifest)
        for status in ("in_progress", "partial", "completed", "blocked", "superseded"):
            for owner, field, value in (
                ("manifest", "finalized_at", "2025-12-31T23:59:59Z"),
                ("execution", "started_at", "2026-01-01T00:00:30Z"),
                ("execution", "started_at", "2025-12-31T23:59:59Z"),
                ("execution", "finished_at", "2026-01-01T00:01:30Z"),
            ):
                with self.subTest(status=status, owner=owner, field=field, value=value):
                    self.manifest = copy.deepcopy(original)
                    execution = {**self.execution, "status": status}
                    target = self.manifest if owner == "manifest" else execution
                    target[field] = value
                    self.validate(execution, False, owner)

    def test_time_order_keeps_equal_instants_and_late_evidence(self):
        for manifest_status in ("approved", "superseded"):
            for kind in ("command", "manual"):
                for finalized, started, accepted in (
                    ("2026-01-01T08:02:00+08:00", "2026-01-01T00:02:00Z", True),
                    ("2026-01-01T08:02:00+07:00", "2026-01-01T00:02:00Z", False),
                    ("2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z", True),
                ):
                    with self.subTest(manifest_status=manifest_status, kind=kind, finalized=finalized):
                        self.manifest.update(status=manifest_status, finalized_at=finalized)
                        execution = self.manual_execution() if kind == "manual" else copy.deepcopy(self.execution)
                        execution.update(started_at=started, finished_at=started)
                        # recorded_at is actual recording time, possibly after completion.
                        for record in execution["tasks"][0]["commands"] + execution["tasks"][0]["tests"] + execution["cumulative_verification"]:
                            record["recorded_at"] = "2026-01-02T00:00:00Z"
                        self.validate(execution, accepted)

    def test_time_order_keeps_unresolved_template_and_unfinalized_approval(self):
        self.manifest = json.loads((SKILL / "assets/manifest-template.json").read_text())
        execution = json.loads((SKILL / "assets/execution-template.json").read_text())
        self.validate(execution, True)
        for finalized in (None, "{{INPUT:ISO-8601-or-null}}"):
            with self.subTest(finalized=finalized):
                self.manifest.update(status="approved", approved_at="2026-01-01T00:00:00Z", finalized_at=finalized)
                self.validate(execution, True)

    def test_finish_time_order_uses_timezone_instants(self):
        for finished, accepted in (
            ("2026-01-01T08:02:00+08:00", True),
            ("2026-01-01T08:02:00+09:00", False),
            ("2025-12-31T23:02:00-01:00", True),
            ("2026-01-01T00:03:00Z", True),
            ("2026-01-01T00:01:59Z", False),
        ):
            with self.subTest(finished=finished):
                self.validate({**self.execution, "finished_at": finished}, accepted)

    def test_invalid_time_values_report_errors_without_comparison_crashes(self):
        original = copy.deepcopy(self.manifest)
        for owner, field in (("manifest", "approved_at"), ("manifest", "finalized_at"),
                             ("execution", "started_at"), ("execution", "finished_at")):
            for value in ("invalid-time", "2026-01-01T00:00:00", []):
                with self.subTest(owner=owner, field=field, value=value):
                    self.manifest = copy.deepcopy(original)
                    execution = copy.deepcopy(self.execution)
                    target = self.manifest if owner == "manifest" else execution
                    target[field] = value
                    self.validate(execution, False, owner)
