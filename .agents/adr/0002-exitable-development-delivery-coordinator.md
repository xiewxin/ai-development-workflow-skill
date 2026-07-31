# 0002: Keep the workflow as an exitable development delivery coordinator

## Status

Accepted.

## Context

`ai-development-workflow` can complete requirement planning, test design, implementation, verification, documentation sync, and Git diff review without an external workflow. External Skills may enter coordination either through proactive discovery from the platform's current catalog or through an explicit user invocation already present in the task context. Their invocation modes, artifact chains, and side effects differ. Treating one Provider as a permanent primary workflow would duplicate its methods and make the native path dependent on its availability; freely mixing every matching Skill would lose authorization, ownership, recovery, and review-convergence guarantees.

The difficult trade-off is how long coordination remains active and when separately owned capabilities may be composed. Persistent orchestration provides governance but adds handoff and documentation cost even when one workflow already covers the request. Immediate delegation or unrestricted composition is efficient on paper but unsafe when several workflows, formal artifacts, or side effects overlap.

## Decision

- Keep the native four-mode workflow complete and Provider-neutral.
- Use only the platform's current catalog for proactive discovery; discovery does not activate, install, or authorize a capability.
- Treat an explicit user invocation as a separate coordination input rather than rediscovering it through the catalog; it still must pass scope, authorization, side-effect, artifact-ownership, and result-consumption checks.
- Keep authorization gates, formal-artifact ownership, resumable User-invoked handoffs, native fallback, and review convergence in `ai-development-workflow`.
- Compose different Providers only across non-overlapping capability slots or an explicit upstream-to-downstream artifact relationship. Keep one primary executor per slot and one writable owner per formal artifact; do not split indivisible capability bundles.
- Require a lightweight artifact handoff contract for each cross-Provider edge: stable upstream identity and owner, read-only input boundary, exact downstream capability, independently owned output, no upstream write-back, return validation, and native fallback. Require a content fingerprint only when cross-task recovery or ambiguous versions make it necessary.
- Exit additional orchestration when one workflow safely and completely covers the request.
- Keep internal matching invisible unless the user must act, authorize, resolve a conflict, or safely resume across tasks.

## Consequences

External Skills can improve individual stages without becoming mandatory dependencies or taking unrelated artifact ownership. An explicitly invoked Skill can safely rejoin delivery even when it was not proactively discovered, while local installation alone still proves nothing. Simple native work remains direct, and compatible cross-Provider chains gain a single ownership, recovery, and review boundary. The cost is a maintained orchestration contract, Provider constraint profiles, and per-edge handoff evidence; they must not become a brand router, static command catalog, duplicated workflow implementation, unrestricted Provider pipeline, or persistent per-stage log.
