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

- **Requirement planning**: Define goals, boundaries, impact, reuse, risks, implementation slices, and acceptance criteria.
- **Test design**: Cover applicable success, boundary, failure, and regression scenarios, then map them to automated and manual verification.
- **Git diff review**: Reconcile the full change set against the approved scope and track findings with stable `REV-*` IDs and high, medium, or low severity.
- **Full workflow**: Plan, design tests, implement after approval, verify, update documentation, and review the final diff.

AI collaboration metrics and local timing are disabled by default. They are enabled only when the user explicitly asks for them or the target repository requires them.

## External Workflow Integration

- Uses verifiable evidence from the current conversation, repository rules, and active artifacts to integrate with Superpowers, Matt Pocock Skills, Spec Kit, OpenSpec, BMAD, or another provider with clear capabilities and ownership.
- Selects one requirement-level primary provider. Secondary providers may only fill independent gaps without duplicating artifact ownership.
- Keeps one writable owner for each external artifact. This Skill records its locator, state, gaps, and synchronization result instead of copying a complete spec, plan, or ticket set.
- Works independently when no external provider is active. An optional provider failure degrades only the affected capability and is never reported as a pass.
- Never installs, initializes, archives, publishes, or performs remote writes through an external workflow without the required authorization.

For Matt Pocock Skills, installation alone does not activate the provider. Existing `to-spec` or `to-tickets` artifacts can own their approved content, while this Skill fills planning and verification gaps. A workflow such as `implement` that may create a commit also requires separate commit authorization.

## Requirement Planning Features

- Investigates discoverable facts before asking questions, then confirms only decisions that can change scope, contracts, architecture, test seams, or acceptance criteria.
- Adds user-observable behavior and acceptance scenarios only when they help define the requirement; it does not generate long user-story lists to fill a template.
- Chooses the highest stable user-observable public interface as the preferred test seam. If an existing lower-level test cannot verify the visible contract, a new test may be added at that public interface with approval.
- Organizes work into independently verifiable vertical slices with blockers and completion criteria. Wide refactors use `expand → migrate → contract` with an integration gate.

## Reference Timing and Productivity

- Timing is opt-in and records only time; it never collects, estimates, or reports token usage.
- It uses short Python 3 standard-library commands and local session state, without a background service or cloud upload.
- Productivity is calculated only when complete measured coverage and a valid pre-implementation PERT baseline match. Partial or unknown coverage reports measured time and anomalies without inventing a percentage.
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
- “Complete this feature using the full workflow and pause at every approval gate.”

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

The validator checks the public working tree, excluding `.git` and `.idea`, for the Skill structure, metadata, timing script, relative Markdown links, required template fields, Traditional Chinese repository documents, and likely sensitive information. It reports only file paths, rules, and necessary line numbers, without echoing matched content.

The Skill's interaction language follows the user. Generated files and code follow the target repository's rules and nearby conventions. The Traditional Chinese publication check protects this repository's public Chinese documents and does not impose that language on target repositories.

## Security and Privacy

- Public examples use fictional, neutral data.
- Do not commit real business data, personal information, credentials, internal URLs, or local machine paths.
- Publication validation is a safety aid and does not replace manual diff review or GitHub Secret Scanning.

## License

This project is available under the [MIT License](LICENSE).
