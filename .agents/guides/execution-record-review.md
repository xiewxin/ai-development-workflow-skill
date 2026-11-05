# Execution-record validation review

Use this guide when changing lifecycle, observation, identity or completion checks in `scripts/validate-publication.sh`. The behavior contract remains in `skills/ai-development-workflow/references/plan-package.md`; do not create a second schema here.

## Regression coverage

Start from a valid record and change one relevant dimension at a time. Run the actual validator on temporary Skill copies; do not verify behavior by searching source text.

| Changed boundary | Required neighboring cases |
| --- | --- |
| Lifecycle | Root and Task status, pending and observed nested records, cumulative verification, changes/reviews/commits |
| Lifecycle time | Approval, finalization, start and finish ordering; equal instants, timezone offsets, unresolved templates and late evidence recording |
| Template allowance | The same field before and after observation; automatic and manual records; Task and cumulative locations |
| Identity | Draft and finalized packages, unresolved and concrete bindings, readable historical records |
| Completion | Failed and successful linked observations, same-Task ownership, RED→GREEN history, distinct cumulative checks |

Use literal expected outcomes derived from the contract. Keep valid legacy records, optional fields, `.` and ordinary relative paths as controls. Extend the relevant rows of `tests/test_execution_observations.py`; do not invent a new harness or exhaust unrelated combinations.

A reported counterexample needs a failing regression before the fix. For a guard change, also check the adjacent branch that bypasses that guard and the other collection that uses the same helper. Passing existing tests does not establish that these combinations are covered.

## Review and completion claims

After a lifecycle guard changes, review the complete candidate and its contracts, including untracked files and inherited changes. A review brief must identify that candidate and the neighboring-case matrix; it must not limit the reviewer to confirming the reported example. Keep review read-only and preserve raw evidence.

Record separately whether the reported findings are closed, which complete candidate was reviewed, which checks actually ran, and which behavior remains unverified. A focused review or a passing static suite must not be described as complete delivery verification. Do not claim real approval, materialization, provider execution or efficiency from template validation.
