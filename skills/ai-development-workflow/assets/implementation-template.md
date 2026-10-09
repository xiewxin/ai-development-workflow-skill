# {{INPUT:主題}} Implementation Plan

> **For agentic workers:** {{INPUT:只填已核准 execution_mode 的指令；相容性通過後才指定 REQUIRED SUB-SKILL superpowers:executing-plans 或 superpowers:subagent-driven-development；inline/provider 填對應執行者，不保留 Superpowers 必用指令}}。每個步驟約 2–5 分鐘，checkbox 是步驟清單，實際進度記於 execution.json。

**Goal:** {{INPUT:一行描述要完成的可驗證成果}}

**Architecture:** See [design.md]({{INPUT:./design.md}}). Do not restate design decisions here.

**Tech Stack:** {{INPUT:精確技術、版本與必要函式庫}}

**Spec:** [design.md]({{INPUT:./design.md}}) and [delivery.md]({{INPUT:./delivery.md}})

**Review Focus:** {{INPUT:最高風險的合同、資料、相容性或副作用邊界}}

**Delivery contract:** See [delivery.md]({{INPUT:./delivery.md}}) for scope, evidence, `AC-*`, risks, and final acceptance.

**Test design:** See [test-design.md]({{INPUT:./test-design.md}}) for the test matrix, data, assertions, and `RUN-*` commands.

**Execution policy:** `execution_mode={{INPUT:inline|executing-plans|subagent-driven-development|provider}}`; `worktree_policy={{INPUT:current-checkout|isolated-worktree}}`; `commit_policy={{INPUT:none|task-local-commits|final-local-commit}}`. The approved values must match `manifest.json`.

## Global Constraints

- {{INPUT:機械摘錄 design.md 或 delivery.md 中影響執行的全域限制與 exact values，包含介面/schema、邊界和精確路徑，並附來源章節；不可只留連結}}
- Approved source revision: `{{INPUT:完整 Git source_revision SHA}}`. Execution ID: `{{INPUT:single-execution-id}}`. These values must match manifest.json and the external approval record.
- Allowed external actions: push, PR, merge, release, publish, deployment, API mutations, and other remote writes require separate authorization.
- Record observed commands, tests, task status, and commit SHA only in `execution.json`.
- Assign a unique observed run_id to every command attempt, including RED/GREEN retries and cumulative verification. Keep planned_run_id as the source RUN ID (null for non-test operations), and bind each test result to an existing observed command run_id.
- Before execution, verify the external approval record and final receipt, manifest SHA, every allowlisted file SHA, finalized_at, and execution/worktree/commit policies. Complete materialization before starting a worktree-bound executor.
- Approved Markdown and manifest are immutable: do not check off boxes or rewrite status, steps, or hashes. Provider ledger/todos are recovery indexes tied to the full plan path, package ID, and manifest SHA; reconcile their evidence to execution.json.
- STOP for reapproval if scope, AC, interfaces, design, implementation steps, allowed files, execution mode, worktree policy, or authorization must change. Record the original step, new fact, impact, and resolution in execution.json; a Provider ruling cannot authorize such a change. Failed commands require an already approved alternative or a stop.
- Use only an executor that satisfies the approved policies, including local commits, ledger recovery, and the conservative deviation rule. An incompatible Provider is ineligible.
- Every verification command is a mechanical excerpt of its `RUN-*` entry in test-design.md, with the same workdir, command, and Expected. Resolve and compare excerpts before approval; do not maintain independent command definitions.
- Before the first implementation change, require `git rev-parse HEAD` to equal the approved source_revision, claim the single execution receipt in the latest external approval state, then record HEAD as `execution.json.base_commit_sha`. Inventory pre-existing staged, unstaged, and untracked changes. Preserve unrelated edits; if overlapping changes cannot be distinguished safely, stop before implementation. Never restart a completed, revoked, or superseded execution; resume only the matching claimed execution ID and worktree.

## File Map

| Path | Responsibility | Change |
| --- | --- | --- |
| `{{INPUT:exact/path/to/file.ext}}` | {{INPUT:檔案單一責任}} | {{INPUT:create|modify|test|document}} |

---

### Task 1: {{INPUT:可獨立驗證的元件或行為}}

**Traceability:** `S-01`; `AC-01`; `T-01`

**Required brief context:** The controller must carry this Task verbatim together with the complete Global Constraints and Execution policy (including exact values), Spec context, and required dependency interfaces. Verify that context before dispatch; a Task-only extraction is not a sufficient brief.

**Brief boundary:** End this Task at the next same-or-higher-level heading outside fenced code. Keep the final cumulative verification and branch review with the controller, even if a Provider extractor includes them after the last Task. Preserve the raw extract and verify the mechanically assembled dispatch brief against its source.

**Evidence handoff:** {{INPUT:指定 execution.json 的單一寫入者及責任交還時點；若委派實作代理回填，提供 commands/tests/deviations 完整欄位合同與可定位範本；否則由實作代理交回原始觀測，由協調者回填。recorded_at 使用實際記錄時間，未採集的歷史執行時間明示缺口，不推算。}}

**Files:**
- Create: `{{INPUT:exact/path/to/new-file.ext}}`
- Modify: `{{INPUT:exact/path/to/existing-file.ext}}` at `{{INPUT:symbol or verified locator}}`
- Test: `{{INPUT:exact/path/to/test-file.ext}}`

**Allowed files:** `{{INPUT:列出本 Task 唯一允許修改的精確路徑}}`

**Interfaces:**
- Consumes: `{{INPUT:完整 signature、schema 或前置 Task 產物；無則寫 None}}`
- Produces: `{{INPUT:完整 function/class/route/schema、參數與回傳型別}}`

**Dependencies:** `{{INPUT:None 或 Task ID 加上實際依賴原因}}`

**Dependency gate:** {{INPUT:無依賴則寫 None；否則在啟動前核對同一 execution.json 中各前置 Task 已 completed、測試與 Task Diff review 通過、所需介面可用，並具備 commit_policy 要求的真實 commit；記錄證據定位。缺失或 pending 時停止，不以程式碼已存在代替。}}

**Task baseline:** Before the first write, record `git rev-parse HEAD` and the staged/unstaged/untracked inventory in execution evidence. Use this Task-start snapshot to distinguish this Task's changes from predecessor or pre-existing changes; do not reset the snapshot on resume.

- [ ] **Step 1: Write the failing test**

```{{INPUT:language}}
{{INPUT:完整且可執行的測試程式碼；不得使用省略號或占位敘述}}
```

- [ ] **Step 2: Run the focused test and verify RED**

Workdir: `{{INPUT:repository-relative working directory}}`

Run: `{{INPUT:exact focused test command}}`

Expected: FAIL with `{{INPUT:證明缺少目標行為的精確訊息或斷言差異}}`, not a syntax, fixture, or environment error.

- [ ] **Step 3: Write minimal implementation**

```{{INPUT:language}}
{{INPUT:使 Step 1 通過的完整最小實作；不得使用省略號或占位敘述}}
```

- [ ] **Step 4: Run the focused test and verify GREEN**

Workdir: `{{INPUT:repository-relative working directory}}`

Run: `{{INPUT:exact focused test command}}`

Expected: PASS with `{{INPUT:精確測試數、摘要或 exit code}}` and no new warnings.

- [ ] **Step 5: Refactor while staying GREEN**

Action: {{INPUT:精確的小型重構；若不需要，明示以 Step 3 為最小完成狀態}}

Run: `{{INPUT:exact focused test command}}`

Expected: PASS with the same observable behavior.

- [ ] **Step 6: Review the task diff**

Run: `git status --short --untracked-files=all && git diff -- {{INPUT:space-separated allowed files}} && git diff --cached -- {{INPUT:space-separated allowed files}}`

Expected: only this Task's allowed files changed; every hunk maps to `S-01`, `AC-01`, or `T-01`; no secrets or unrelated edits. Compare against the recorded Task-start HEAD and inventory, including any already committed Task changes on resume. Read each new untracked allowed file in full, since neither diff command shows it; do not stage files merely to make them visible. Preserve pre-existing unrelated changes and stop if attribution is unclear. Record review passed only after staged, unstaged and new-file content have all been inspected.

- [ ] **Step 7: Record task evidence, optionally commit, then bind the commit**

Update: `execution.json` Task `S-01` with actual commands, timestamps, tests, evidence, changed files, and review result. Keep `commit_sha=null` until a commit actually exists.

If and only if `commit_policy=task-local-commits`:

```bash
git add {{INPUT:exact allowed paths}}
git commit -m "{{INPUT:exact local commit message}}"
```

Expected: one local commit containing only the allowed files. This does not authorize push or PR creation.

After the command succeeds, read `git rev-parse HEAD` and update only `execution.json` Task `S-01.commit_sha` with that observed SHA. If no commit is authorized, retain `null`.

---

## Final cumulative verification

- [ ] **Run cumulative verification**

Workdir: `{{INPUT:repository-relative working directory}}`

Run:

```bash
{{INPUT:exact full verification command sequence}}
```

Expected: `{{INPUT:完整套件、lint、build 與 publication checks 的精確成功摘要或 exit code}}`.

- [ ] **Review the complete diff**

Run: `git diff --check {{INPUT:execution.base_commit_sha}} && git status --short && git diff {{INPUT:execution.base_commit_sha}} -- {{INPUT:all approved paths}}`

Expected: no whitespace errors; review includes committed, staged, and unstaged changes since the recorded base; all implementation hunks map to `AC-*／S-*／T-*`. Compare status with the initial inventory and inspect every new untracked allowed file separately, since git diff omits it; do not add files merely to make them visible in the diff. Preserve and exclude pre-existing unrelated edits from this delivery claim.

- [ ] **Create the final local commit only when authorized**

If and only if `commit_policy=final-local-commit`, stage exactly the approved implementation paths, create the planned local commit, verify it with `git show --stat --oneline HEAD`, and record the observed SHA in `execution.json.final_commit_sha`. Otherwise do not commit. Push and PR creation remain separately authorized.

- [ ] **Finalize execution evidence**

Update `execution.json` with cumulative commands, test results, final review, actual commit SHA values, deviations, remaining risks, and completion time. Do not alter approved plan facts to make execution appear compliant.
