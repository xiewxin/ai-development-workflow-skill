# AI Development Workflow Skill

English | [繁體中文](README.md)

An open-source Agent Skill for Codex and Claude Code that provides a verifiable workflow for requirement planning, test design, Git diff review, and end-to-end implementation.

## Technology and Compatibility

- Skill format: Agent Skills (`SKILL.md`)
- Supported tools: Codex and Claude Code
- Documentation formats: Markdown and YAML
- Publication validation: Bash and the Python 3 standard library
- Version control and review: Git

## Four Modes

- **Requirement planning**: Define goals, boundaries, impact, reuse, risks, implementation slices, and acceptance criteria. Existing relevant domain context and ADRs are read when present, but never created just to satisfy the workflow.
- **Test design**: Cover applicable success, boundary, failure, and regression scenarios, then map them to automated and manual verification.
- **Git diff review**: Independently inspect Spec/scope compliance and Standards/engineering quality, then verify and deduplicate findings into stable `REV-*` IDs with high, medium, or low severity.
- **Full workflow**: Plan, design tests, implement after approval, verify, update documentation, and review the final diff.

AI collaboration metrics and local timing are disabled by default. They are enabled only when the user explicitly asks for them or the target repository requires them.

## External Workflow Integration

- The four modes remain a complete native path. External capabilities are evaluated during requirement planning, test design, implementation, verification and repair, documentation sync, and Git diff review only after the user enters a mode or explicitly requests cross-Skill delivery coordination.
- Capabilities have two inputs. Proactive discovery reads only the Skill catalog metadata provided by the platform for the current task. An explicit invocation context accepts a capability the user has already invoked through the platform without rediscovering, ranking, or invoking it again. Discovery is not activation, and neither input scans local Skills or treats installation state, brands, or names as capability evidence.
- With zero, one, or multiple capabilities pending verification, the fast path falls back immediately, avoids a fake comparison, or expands only the current highest-priority group. Metadata filtering does not itself create a candidate; authorization, side effects, ownership, mandatory contracts, and verifiable value remain required on every path.
- Candidates must pass availability, invocation-mode, authorization, side-effect, artifact-ownership, and mandatory-contract gates before verifiable value and a consistent priority order can select one. The native workflow remains silent and complete when none qualify.
- Model-invoked capabilities follow the platform contract. A User-invoked capability produces one currently executable handoff action and pauses; the returned artifact is revalidated before work resumes. The README does not maintain a static third-party command catalog.
- Each requirement has at most one requirement-level workflow owner. Stage capability executors fill independent slots without taking unrelated artifact ownership, and every formal artifact keeps one writable owner.
- The cross-provider composition rule permits only non-overlapping capability slots or an explicit upstream/downstream relationship. One primary executor owns each slot or indivisible bundle, and every cross-provider edge requires a lightweight artifact handoff contract.
- An approved plan is not sent to a ticket generator by default. Task-ordering handoff is useful only when long-lived tracking, complex collaboration, or an external tracker adds verifiable value.
- Orchestration details are shown or persisted only when the user must act, grant additional authorization, resolve an artifact conflict, or safely resume across tasks. Internal snapshots, rankings, and rejected candidates do not become plan fields.
- When one external workflow safely and completely covers the request, this Skill exits extra orchestration. Failures degrade according to actual side effects and are never reported as provider success.
- The integration never installs, sets up, initializes, commits, archives, deletes, performs remote writes, or publishes without explicit authorization.

For Matt Pocock Skills, installation alone does not create a candidate. Existing `to-spec` or `to-tickets` artifacts may retain their approved ownership, while `to-tickets` remains conditional and User-invoked. A workflow such as `implement` that may create a commit is ineligible unless the approved plan package explicitly grants a compatible local `commit_policy` or the user grants commit authorization separately.

## Requirement Planning Features

- Every new requirement gets a `docs/plans/YYYY-MM-DD-<topic>/` package. `design.md`, `delivery.md`, `implementation.md`, `test-design.md`, `manifest.json`, and `execution.json` have separate ownership; legacy flat plans are read-only compatibility inputs and are never moved or deleted automatically.
- `implementation.md` is the single execution entry point. Superpowers `executing-plans` or `subagent-driven-development` can consume it without format conversion after passing the [compatibility matrix](skills/ai-development-workflow/references/plan-package.md#superpowers-相容性矩陣).
- An external approval record binds the four formal Markdown SHA-256 hashes, source revision, execution ID, and execution, worktree, and local commit policies. After optional task derivation, finalize `manifest.json` and record its single-execution receipt. Approved documents stay immutable and the latest external state controls their validity; `execution.json` owns observed commands, tests, task status, and commit SHAs.
- `docs/plans/` remains Git-ignored and must not be committed. Isolated-worktree materialization copies only the manifest allowlist to the same relative path and revalidates it before copying, after copying, and before execution. Push, PR, merge, release, publish, deployment, and other remote writes always require separate authorization.
- `tasks/` is absent by default. It is derived from the approved `implementation.md` only for parallel, cross-session, cross-repository, or high-risk isolation work, and each task binds its parent SHA, task ID, acceptance criteria, dependencies, and allowed files.
- Investigates discoverable facts before asking questions, then confirms only decisions that can change scope, contracts, architecture, test seams, or acceptance criteria.
- Reads existing relevant domain context, context maps, and ADRs on demand, verifies them against current code, and does not create extra decision documents merely to fill a format.
- Adds user-observable behavior and acceptance scenarios only when they help define the requirement; it does not generate long user-story lists to fill a template.
- Uses a compact profile for small single-repository work without external artifacts or high-spread risk. The legacy six core plan headings are historical reading guidance; new packages distribute content by artifact ownership and may use five core test-design headings. Complex work expands the field catalog only when needed.
- Connects acceptance, slices, scenarios, data, and execution through `AC-* → S-* → T-* → D-* / RUN-*`. Planned commands belong to the test design; observed commands and per-scenario results belong only to `execution.json`.
- Chooses the highest stable user-observable public interface as the preferred test seam. If an existing lower-level test cannot verify the visible contract, a new test may be added at that public interface with approval.
- Organizes work into independently verifiable vertical slices with blockers and completion criteria. Wide refactors use `expand → migrate → contract` with an integration gate.

## Reference Timing and Productivity

- Timing is opt-in and records only time; it never collects, estimates, or reports token usage.
- It uses short Python 3 standard-library commands and local session state, without a background service or cloud upload.
- A pre-implementation PERT baseline may cover the full requirement or, when timing is enabled late but before implementation, the next not-yet-started delivery phases. Excluded phases use `0/0/0`, and a remaining-scope result must not be presented as whole-requirement productivity.
- Time savings are calculated only when the declared scope has complete measured coverage and a matching baseline. Reports label the formula as a reference time-saving percentage; partial or unknown coverage reports measured time and anomalies without inventing a percentage.
- When an approved V2 or V3 scope is added after completion in the same conversation, it receives an independent measurement segment. Completed state is not resumed, and segments are not manually merged.
- A new conversation does not search for, resume, or merge previous measurements.
- ActivityWatch can be used only when already installed and explicitly selected. Failures fall back to session timing.

## Installation

### Recommended: skills CLI

Node.js and `npx` are required:

```bash
npx skills add https://github.com/xiewxin/ai-development-workflow-skill.git \
  --skill ai-development-workflow
```

To install globally for Codex and Claude Code:

```bash
npx skills add https://github.com/xiewxin/ai-development-workflow-skill.git \
  --skill ai-development-workflow \
  -g -a codex -a claude-code -y
```

Open a new conversation after installation so the tool can load the Skill.

### Codex built-in installer

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo xiewxin/ai-development-workflow-skill \
  --path skills/ai-development-workflow
```

### Manual copy

From the repository root:

```bash
mkdir -p ~/.codex/skills
cp -R skills/ai-development-workflow ~/.codex/skills/ai-development-workflow
```

For Claude Code:

```bash
mkdir -p ~/.claude/skills
cp -R skills/ai-development-workflow ~/.claude/skills/ai-development-workflow
```

## Usage Examples

- “Create a requirement plan for this change, but do not implement it yet.”
- “Create a test design from the approved plan, including test data and regression scope.”
- “Review the complete Git diff against the target branch.”
- “Use the full workflow for this request. If the current platform provides a collaboration Skill with verifiable value, give me one explicit handoff only when I need to act or authorize it.”
- “Complete this feature using the full workflow, and pause for plan approval, required user actions, additional authorization, or conflict resolution.”

## Updating

For a project-level installation:

```bash
npx skills update ai-development-workflow
```

For a global installation:

```bash
npx skills update ai-development-workflow -g
```

Open a new conversation after updating.

## Publication Validation

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
bash tests/test-validate-publication.sh
bash scripts/validate-publication.sh
```

In repository mode, the validator checks the public working tree while excluding `.git`, `.idea`, and the explicitly Git-ignored process-artifact directories `docs/plans/` and `docs/specs/`. Similar public directories remain in scope. It validates the Skill structure, metadata, timing script, relative Markdown links, required template fields, Traditional Chinese repository documents, and likely sensitive information, reporting only file paths, rules, and necessary line numbers without echoing matched content.

The Skill's interaction language follows the user. Generated files and code follow the target repository's rules and nearby conventions. The Traditional Chinese publication check protects this repository's public Chinese documents and does not impose that language on target repositories.

## Security and Privacy

- Public examples use fictional, neutral data.
- Do not commit real business data, personal information, credentials, internal URLs, or local machine paths.
- Publication validation is a safety aid and does not replace manual diff review or GitHub Secret Scanning.

## License

This project is available under the [MIT License](LICENSE).
