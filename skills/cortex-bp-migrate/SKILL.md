---
name: cortex-bp-migrate
description: Blueprint-to-C++ migration pipeline with conversational analysis, plan-driven execution, visual progress tracking, and hard gates. Supports --audit, --resume, and --fast (streamlined mode for simple migrations).
---

# Blueprint to C++ Migration

You are migrating a Blueprint to C++. You already know how to plan and execute migrations — this skill defines the **contract** (flags, gates, artifacts, agent dispatch) and the **tool truths you cannot derive**. Apply your own judgment everywhere else.

One discipline rule above all: **verify every external premise against the project before repeating it** — ticket claims like "docs mention class X" or "class Y exists" get confirmed with a native grep / reflection query, never echoed. And ground every status claim in a tool result from this session.

## Entry Point

Parse user input for:
- **Blueprint path** (required) — e.g., `BP_JumpPad` or `/Game/Blueprints/BP_JumpPad`
- **`--audit`** — run analysis + design only, save the migration report, present the design, stop. With `--fast`: also report fast-mode eligibility, still stop.
- **`--fast`** — streamlined flow: one approval gate (after the plan) instead of four, auto-defaults for the goal questions (Goal "Reusability / base class", Constraints none, Scope everything), inline verification, auto-archived backup. Eligibility is checked after analysis; if ineligible, report which criteria failed and continue in the full pipeline with the same auto-defaults — do NOT re-ask goal questions.
- **`--resume`** — resume from `docs/migration/blueprint-to-cpp/{BP_Name}/migration-plan.md` frontmatter (`status`, `current_task`, `failed_task`, `phase`, `mode`, `goal`, `redesign_tier`, `blueprint_hash`). Verify state first: files in `files_created` exist, the `_Migration` copy exists, the C++ class compiles, `blueprint_hash` still matches. Offer resume / rewind / restart.

## Pre-Flight

Run `/cortex-editor` (Skill tool) before pipeline start and before every agent dispatch — editor alive, MCP connected, `blueprint` domain registered. Editor lifecycle goes ONLY through `/cortex-editor`; never launch or probe the editor with raw bash. Builds go through `/cortex-build`.

Restart cap: track `editor_restarts` in frontmatter; hard stop at 3 and hand control to the user (usually an underlying engine/plugin issue).

## Hard Rules

1. **`analyze_blueprint_for_migration` is the inventory source of truth.** Never infer structure from `get_info` — it can omit the SCS components array entirely, making a Blueprint look component-less while it owns a real `DefaultSceneRoot`.
2. **Ground truth before code.** Inspect every migrating graph with `graph_list_nodes` + `graph_get_node`, ALWAYS `compact=false` (compact strips hidden world-context/class pins and positions; missing hidden pins = wrong generated C++). Macro graphs, delegate signature graphs, and collapsed subgraphs are NOT reachable — flag them for manual review.
3. **1:1 faithful translation.** Every generated C++ call must map to a Ground Truth Table row. Anything extra is an IMPROVEMENT: present faithful and improved versions separately, faithful is the default, improvements apply only on an explicit user choice at the plan gate. A missing C++ equivalent for a table row is an ERROR — fix before presenting the gate.
4. **Never invent values.** All defaults come from the pre-migration snapshot. C++ component names must match SCS variable names exactly. Display names are not C++ names — resolve `K2_` prefixes via reflection when in doubt.
5. **Hard gates** (AskUserQuestion, never crossed without explicit approval). Full mode: design approval → plan approval → verification review → swap. Fast mode: one gate after the plan.
6. **Pick the migration path by risk, not by habit:**
   - **In-place reparent** (no duplicate, no rename swap): only logic/stub deletions migrate, no BP-declared variables or functions move, no SCS archetype risk, and referencers are unaffected by a reparent. The duplicate→swap choreography is pure overhead here.
   - **Duplicate → execute on copy → verify → rename-swap + fixup redirectors**: everything else.
7. **Referencer claims need two tools.** Confirm `get_referencers` results with a raw content-grep style check before any swap/deletion decision — a single tool's "0 references" is unverified.
8. **Frontmatter after every task**, before starting the next. `migration-plan.md` is the durable resume store; in-session task lists are ephemeral. On failure set `status: failed` + `failed_task` FIRST, then present options.
9. **Phase agents run at sonnet minimum** (frontmatter-enforced). Never dispatch haiku for MCP work — it confuses TCP command names with MCP tool names.

## Fast Mode Eligibility (ALL must be true)

| Criterion | Check | Source |
|-----------|-------|--------|
| High confidence | `migration_confidence` = "high" | `analyze_blueprint_for_migration` |
| No external dependents | `referencers` = 0 | `get_referencers` |
| No child Blueprints | `blueprint_children_count` = 0 | `analyze_blueprint_for_migration` |
| No timelines | `timelines` empty | `analyze_blueprint_for_migration` |
| No event dispatchers | `event_dispatchers` empty | `analyze_blueprint_for_migration` |
| No interfaces | `interfaces_implemented` empty | `analyze_blueprint_for_migration` |
| C++ parent class | Parent path starts `/Script/` | `analyze_blueprint_for_migration` |
| No structural ConstructionScript | UCS has only visual-sync nodes | analysis + graph inspection |
| Single pass | No HIGH-risk deferrals | functional group analysis |
| Not redesign goal | Goal ≠ "Redesign/restructure" | user-selected goal |

The same criteria (with `referencers`/`children` relaxed) classify `complexity: simple` vs `complex`, which selects inline vs agent verification.

## Artifacts

Everything lives in `docs/migration/blueprint-to-cpp/{BP_Name}/` — at most 3 files:

- **`migration-plan.md`** — single source of truth, updated through all stages. YAML frontmatter fields: `blueprint`, `target_class`, `target_header`, `target_source`, `status`, `current_task`, `total_tasks`, `failed_task`, `phase`, `created`, `last_updated`, `blueprint_hash`, `migration_pass`, `total_planned_passes`, `deferred_groups`, `tasks`, `files_created`, `files_modified`, `editor_restarts`, `complexity`, `goal`, `mode`, `redesign_tier`, `target_classes`. Section headings (agents depend on these names): `## Pre-Migration Snapshot`, `## Design Decisions`, `## Migration Scope`, `## Ground Truth Table`, `## Generated C++ Code`, `## Task List`, `## Execution Log`, `### Node Mappings`, `## Verification Results`, `## Final Report`; redesign adds `## Responsibility Groups`, `## Architecture Proposal`, `## Responsibility Map`, `## Integration Points`, `## Manual Migration Steps`.
- **`design.md`** — only for multi-pass migrations, HIGH-risk items (timelines/dispatchers/interfaces), or deferred groups needing explanation.
- **`rollback.json`** — written by the finalizer.

Append idempotently: locate the `##` heading, replace that section if present, else append; update `phase` + `last_updated` in the same edit. Generated C++ lives inline in the plan document (fenced blocks under `### Header ({ClassName}.h)` / `### Source ({ClassName}.cpp)`) — extract by heading when writing to disk. No `generated/` directory except for 4+-file redesigns.

## Ground Truth Table

| Node ID | Display Name | Type | Function/Property | Target | Parameters | Notes | Target Class | Automated |
|---------|-------------|------|-------------------|--------|------------|-------|-------------|-----------|

One row per node in every migrating graph. `Node ID` is for MCP calls only — user-facing output always uses `Display Name`. Record per node class: CallFunction (exact function + hidden pins), DynamicCast (target class), VariableGet/Set, ComponentBoundEvent (needs `AddDynamic`, not a direct call), CallDelegate/AssignDelegate, latent calls (need FTimerHandle/async treatment). For redesign, `Target Class` follows the responsibility map and Tier-3 secondary-actor rows get `Automated: No` (executor leaves them annotated).

## Pipeline

### 1. ANALYZE
Goal questions one at a time via AskUserQuestion (skip with `--fast`): why migrate / constraints / scope. Then MCP analysis: `analyze_blueprint_for_migration`, `get_referencers`, `query_class_hierarchy`, `query_class_context`. Classify each element logic-vs-cosmetic (cosmetic-only — decorative visuals nothing reads — stays in BP; see `resources/cpp-migration.md`), risk (timelines HIGH, dispatchers MEDIUM, simple events LOW), and UCS nodes (visual-sync stays, structural → `OnConstruction()`).

Present: snapshot summary, functional groups (max 6), SAFE/WARNING/BREAKING dependency impact per public member, and explicit MIGRATING / STAYING / DEFERRED columns with reasons. Anti-over-engineering: never recommend migrating spatial construction, visual setup, or component configuration regardless of scope.

**Redesign goal** (when selected): group items by responsibility, scan for existing C++ overlap (merge into existing classes over generating duplicates), classify Tier 1 component extraction / Tier 2 subsystem-or-library / Tier 3 actor split — always prefer the lowest tier; any actor-instance-state reference forces Tier 1; UCS logic cannot extract to components; Tier 3 is rare and its secondary-actor placement is manual. Map every item to a target class; present integration patterns (owner→component: cached `UPROPERTY()` pointer; component→owner: `GetOwner<T>()` or interface; one-to-many: dynamic multicast delegate; component→component: owner mediation — never direct `FindComponentByClass` coupling) and list STAYING nodes that need rewiring to component accessors.

**GATE: design approval** (approve / adjust scope / adjust tier / cancel). On approval write `migration-plan.md`. Always save the full recommendation to `migration-report.md` in the same folder. `--audit` stops here.

### 2. PLAN
Build the Ground Truth Table (Hard Rule 2). Generate complete header + source (+ Build.cs patch): `Super::` calls where applicable, construction script → `OnConstruction()` override (not constructor) unless visual-sync-only, timelines → `UTimelineComponent` + curves in BeginPlay, dispatchers → `DECLARE_DYNAMIC_MULTICAST_DELEGATE`, project coding standards throughout. Redesign generates one file pair per target class, same module only; forward-declare across classes, full includes in `.cpp` only.

Cross-reference per Hard Rule 3. Generate the task list — every task carries **Action / Verify / Rollback**. Task sequence template (adapt counts to the BP):
PREPARE: verify MCP → staleness check → Build.cs → duplicate BP → write header → write source → UBT build → `/cortex-editor` restart + class-registration check. EXECUTE (on the copy): collision validation → reparent → disconnect migrated events + delete orphans → remove functions (dependency order) → remove variables (reverse-dependency) → remove SCS components → smoke test. VERIFY: structural verification → dependency impact check. SWAP: disable auto-save → rename swap → remove orphaned nodes → save → fixup redirectors → re-enable auto-save. COMPLETE: final report. In-place-reparent path (Hard Rule 6) drops the duplicate/swap tasks.

**GATE: plan approval** (approve and execute / review code / adjust / cancel; faithful-vs-improvement choice first if flagged).

### 3. EXECUTE
PREPARE tasks run inline in the orchestrator — never dispatch an agent for file ops, builds, or status checks. Then dispatch **`cortex-toolkit:bp-migration-executor`** with the relevant plan sections (frontmatter + snapshot + scope + ground truth rows in range + task range) — not the whole file. The executor appends `## Execution Log` + `### Node Mappings`.

Crash recovery: on `editor_crashed` → `/cortex-editor`, increment `editor_restarts` (cap 3), **re-verify asset state before resuming** — mid-EXECUTE: the copy is intact; mid-SWAP: check which referencers already point at the new asset and never blindly re-run `failed_task`.

### 4. VERIFY
`complexity: simple` → inline: compile clean, parent is the target class, component count = snapshot − migrated, migrated variables/functions gone, orphaned nodes 0. `complexity: complex` → dispatch **`cortex-toolkit:bp-migration-verifier`** (snapshot + scope + execution log + node mappings). If any inline check fails unexpectedly, escalate to the verifier agent instead of diagnosing inline.

**GATE: verification review** (swap / fix / pause / abort — abort deletes the copy and the generated files, original untouched).

### 5. SWAP + COMPLETE
Dispatch **`cortex-toolkit:bp-migration-finalizer`** (execution log + node mappings + verification results + task range): rename swap (`BP_Name` → `BP_Name_Backup`, copy → `BP_Name`), fixup redirectors, recompile dependents, verify backup on disk, write `rollback.json`, append `## Final Report`. Backup menu: keep / archive to `/Game/Migration/Backups/` / delete (fast mode auto-archives; `backup_verified: false` → explicit warning, recovery is VCS-only). For multi-pass migrations show deferred groups; note that the next pass needs an editor restart. Simple migrations: remind the user CDO property comparison was skipped — verify runtime behavior.

## Known Artifacts (one-liners)

- `has_tick: true` can come solely from a disconnected Event Tick stub — check connections before generating a Tick override.
- `DefaultSceneRoot` on AInfo-derived BPs (GameMode/GameState/PlayerState/Info) is template clutter — safe to delete during cleanup.
- `SKEL_`/`REINST_` entries in hierarchy results are compilation artifacts, not real children.
- `duplicate_blueprint` works on UBlueprint assets only.
- A failing build after generation: parse the compiler output to the owning generated file; never shotgun-edit.

## Supported Blueprint Types

Actor (C++ base/parent subclass) · Widget (UUserWidget + BindWidget) · Component (UActorComponent/USceneComponent) · FunctionLibrary (UBlueprintFunctionLibrary statics) · Interface (UInterface/IInterface pair).

## References

- Patterns, logic-vs-cosmetic, visual-sync classification: `resources/cpp-migration.md`
- Standards: `docs/unreal-coding-standards.md`
- Design history: `docs/plans/2026-02-27-bp-migration-pipeline-design.md`, `docs/plans/2026-02-26-bp-migration-v5-design.md`
