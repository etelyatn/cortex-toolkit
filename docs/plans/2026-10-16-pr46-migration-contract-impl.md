# PR #46 migration contract implementation

## Scope and execution

Owning repository: cortex-toolkit. Task branch: `docs/pr46-migration-contract`, based on `cc901ae`. No worktrees, parent gitlink commits, plugin changes, version bump, publication or remote closure.

Design: [current-contract adaptation](2026-10-16-pr46-migration-contract-design.md).

The change is an existing-owner documentation refactor, not a new migration execution path. Implement inline; use independent read-only reviews for resource compatibility and safety/ownership preservation.

## Execution status

Implementation was already present when the user requested design review followed by execution. The design and candidate were reviewed independently for state/phase compatibility and safety/ownership preservation; neither review left actionable findings. Resume from this record rather than recreating the implementation.

- [x] Design disposition reviewed, including intentionally excluded lifecycle changes.
- [x] Contract-style skill implemented against the current phase guides.
- [x] Original checklist, widget ownership, guarded operations and durable state preserved.
- [x] Reference-application exercise completed; artifact-count contradiction resolved.
- [x] Candidate reviewed, including removal of the wording-only test.
- [x] Continuation verification: taxonomy, OpenCode packaging and all 29 Python tests passed.
- [x] Packaging acceptance: Codex, taxonomy and OpenCode checks pass after removing the obsolete two-line ban on the manifest's intentional `bash` prefix. Native Windows and POSIX configured-hook smoke also pass; see the verification record for environment limits and broader-suite results.

Evidence and limits: [verification record](../verification/2026-10-16-pr46-migration-contract.md). No unfinished in-scope implementation remains. Preserve the reviewed changes on the local task branch; publication or merge requires a separate instruction.

## Changed surface

`skills/cortex-bp-migrate/SKILL.md` is the only executable guidance surface changed. Keep the original Blueprint/C++ checklist and widget rules intact. Replace duplicated stage prose/examples with:

- Entry/flags, editor lifecycle and evidence boundaries.
- Eligibility and redesign ownership contracts.
- Artifact/frontmatter/section schema and per-task update rules.
- Ground-truth/code generation requirements.
- Full task sequence and exact Fast-1 through Fast-14 table.
- Guarded graph branch, verification/finalization and recovery.

The existing executor, verifier and finalizer resources remain owners of detailed phase protocols. No new agent or helper is created. The pre-existing artifact count contradiction is removed by enumerating all existing artifacts rather than imposing a false maximum.

`tests/test_typed_blueprint_authoring_guidance.py` also loses one wording-only routing test and its now-unused phrase fixture. That test failed on equivalent prose, not a missing behavior. It is removed rather than re-pinned to this rewrite; the fixture/schema tests and remaining routing checks are unchanged.

On the subsequent continuation, `tests/test-codex-plugin.sh` loses only the obsolete two-line rejection of a `bash` prefix. The hook manifest and runtime are unchanged. Actual configured commands were exercised with default-off/no-side-effect checks and enabled context injection on native Windows Git Bash and a POSIX deployment fixture before accepting this validation correction.

## Verification procedure

1. Before editing, exercise a fresh model with no toolkit guidance and another with the original skill, using the same four-case task: audit+fast with an unverified premise; exact fast tasks/state; unavailable/ambiguous guarded prune; widget ownership/localization and durable schema.
2. Observe the no-guidance retrieval failure (cannot substantiate task IDs, artifact paths or schema). Observe the original-skill ambiguity: it requires migration-report.md while also imposing a three-file maximum.
3. Replace the skill, run the same reference-application exercise, and inspect each answer against required decisions. This is simulated guidance usage, not live asset migration or reproduction of contributor A/B scores.
4. Run existing toolkit taxonomy, Codex/OpenCode packaging and typed Blueprint guidance checks. Do not introduce permanent tests that assert the exact rewritten prose.
5. Independently review resource/task compatibility and safety/ownership preservation; confirm actionable findings against actual source and correct them before delivery.
6. Record exact results and remaining runtime limits in `docs/verification/2026-10-16-pr46-migration-contract.md`.

## Recovery

No editor or project asset mutation is needed. Edits are task-owned toolkit Markdown plus obsolete validation removals in the Python guidance and Codex packaging tests. Preserve unrelated parent work and the pre-existing submodule gitlink state; leave the task branch available for inspection. Publication/merge requires a separate instruction.
