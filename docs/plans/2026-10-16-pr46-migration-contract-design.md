# PR #46: current migration contract adaptation

## Decision

Adopt the contract-style documentation refactor proposed by [Boshchuk in PR #46](https://github.com/etelyatn/cortex-toolkit/pull/46), not the stale patch verbatim. This is a documentation-only refactor of the existing migration owner; no native/MCP API, asset lifecycle, approval authority, or supported operation is added.

Reference revisions: current toolkit `cc901ae` (equal to freshly fetched origin/main at intake); contributor head `38bbecce62c8d58e115ce936dca1a5450921f1e1`. PR was open, draft, conflicting, with no checks/reviews/comments. Remote state is evidence, not authority to publish or close it. Requested endpoint: local evaluation/adaptation.

## Per-behavior disposition

| Proposed behavior | Current need and route |
|---|---|
| Contract-style skill instead of repeated procedural narrative | Adopt locally. Keep one compact entry contract and reuse existing phase guides, rather than move the old narrative into another always-loaded file. |
| Verify external premises before repeating them | Adopt. Source/reflection evidence is required; a ticket is not proof that a class exists. |
| Analyze-first inventory; full graph inspection; faithful translation | Retain current contracts and explicitly distinguish capability labels from routed command names. Do not import unverified universal claims about native inventory omissions. |
| Flags, resume state, task IDs, gates and rollback artifacts | Preserve current full/14-task-fast protocols, numeric state IDs, section names, per-task persistence, no-extra-fast-gate behavior and phase guide handoffs. Clarify the pre-existing contradictory three-file maximum: the existing mandatory migration report makes four possible document artifacts. |
| Named phase agents and Sonnet floor | Do not adopt: toolkit now executes in the current session using resource guides, not shipped agent definitions. |
| Automatic in-place migration | Do not adopt. Submitted selection criteria do not define durable path/resume/rollback state and conflict with guides that verify a copy and finalize via swap. Standalone reparent already exists as a tool; adding a second migration lifecycle is not necessary for this refactor. This capability is not represented as implemented or tracked delivery. |
| Two-tool referencer check using raw content grep | Do not adopt as a safety guarantee. Binary asset references are not proved absent by string grep. Preserve existing referencer/dependency checks and fail-closed guarded graph routes. |
| Blanket DefaultSceneRoot deletion and new tool gotchas | Do not import unverified destructive advice from the stale patch. Existing collision/data-loss acknowledgment and approved-scope cleanup remain authoritative. |
| Recent widget/localization and guarded graph guidance | Preserve, including editable presentation, reference-aware binding renames, typed String Table save/reload evidence, complete-or-refuse pruning and stop-and-reconcile. |

## Acceptance

- Main skill is substantially shorter without replacing it with a copy of the old narrative elsewhere.
- Existing phase guides still receive the same plan fields, sections and full/fast task mappings.
- Audit never executes; fast failures do not rerun migration; unavailable/ambiguous bounded mutations cannot fall back to unsafe tools.
- Widget ownership and required completion evidence remain intact.
- Reference-application exercises and existing packaging/guidance checks pass; no Unreal runtime change is claimed.
- Preserve parent workspace changes and leave remote PR state unchanged.

## Packaging continuation

The subsequent request to continue includes resolving the remaining packaging acceptance gap. Source history (`f46f467`) and independent runtime smoke establish that explicit `bash` invocation of the non-executable wrapper is intentional and works on native Windows Git Bash and POSIX. Remove only the obsolete Codex test prohibition on that prefix; do not change the manifest, wrapper, hook opt-in semantics or editor lifecycle. This correction changes validation, not production behavior.

## Attribution

The contract-first organization and external-premise discipline adapt the proposal by Viktar Bashchuk / Boshchuk. His reported A/B scores are contributor evidence, not reproduced maintainer benchmark results. No contributor commit is cherry-picked; the adaptation is against current main.
