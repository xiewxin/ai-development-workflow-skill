# Repository maintenance guide

This repository publishes the `ai-development-workflow` Agent Skill.

## Sources of truth

- `skills/ai-development-workflow/SKILL.md` owns routing and core behavior.
- Files under `skills/ai-development-workflow/references/` own stage-specific contracts.
- Files under `skills/ai-development-workflow/assets/` are reusable output templates.
- `README.md` and `README.en.md` explain the public interface; they must not redefine behavior differently.

## Maintainer guide index

- [`.agents/adr/0001-runtime-boundary.md`](.agents/adr/0001-runtime-boundary.md) records why timing remains an optional Python helper.
- Add a focused child guide only when a repeated, non-obvious maintenance rule would otherwise make this root guide unstable or overly detailed.
- Keep business walkthroughs, temporary plans, release history, and one-off implementation notes out of maintainer guidance.

## Runtime boundary

- Keep the Skill Markdown-first and dependency-light.
- `scripts/measure.py` is an optional, standard-library-only timing helper.
- AI collaboration measurement remains disabled unless explicitly requested or required by repository policy.
- Missing Python disables timing only; it must not block planning, test design, implementation, or review.
- Do not add a mandatory runtime or migrate the timing helper without evidence of a user-facing portability problem.
- See [`.agents/adr/0001-runtime-boundary.md`](.agents/adr/0001-runtime-boundary.md).

## Editing rules

- Preserve progressive disclosure: keep common routing in `SKILL.md` and branch-specific detail in references.
- Keep one source of truth for each rule; link instead of copying.
- Follow the target repository language for generated artifacts. Public repository documents are Traditional Chinese and English as indicated by nearby files.
- Do not publish conversations, credentials, personal data, private repository details, or local absolute paths.
- `docs/plans/` and `docs/specs/` are ignored process artifacts and must not be committed.

## Verification

- Run `python3 -m unittest discover -s tests -p "test_*.py" -v`.
- Run `bash tests/test-validate-publication.sh`.
- Run `bash scripts/validate-publication.sh`.
- Run `git diff --check`.

## Release boundary

- Use a Pull Request for public changes.
- Build release notes from the complete previous-tag-to-candidate range, not only the latest commit or PR.
- Verify that every approved user-observable change is represented before tagging.
- Merge, release, and local Skill update are distinct actions.
