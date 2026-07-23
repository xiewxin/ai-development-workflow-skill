# 0001: Keep timing as an optional Python helper

## Status

Accepted.

## Context

The Skill's core planning, test-design, implementation, and review behavior is declarative Markdown. Reference timing needs deterministic local state, but it is opt-in and may degrade without blocking the core workflow.

The repository supports `npx skills add`, the Codex Python installer, and manual installation. An install tool does not automatically become a universal execution runtime.

## Decision

- Keep the public Skill Markdown-first.
- Keep `measure.py` standard-library-only and optional.
- Do not require Python for the core workflow.
- Do not introduce a second timing implementation in JavaScript.
- Reconsider the runtime only after reproducible portability failures or a deliberate change that makes timing mandatory.

## Consequences

The existing three-platform contract tests remain necessary. Missing Python is an explicit timing fallback, not a failed Skill run.
