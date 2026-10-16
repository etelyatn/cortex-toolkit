---
name: cortex-bp-migrate
description: Use when auditing, planning, executing, or resuming a Blueprint-to-C++ migration, including --audit, --fast, and --resume requests.
---

# Blueprint to C++ Migration

This skill defines the migration contract: ownership, evidence, approval gates, durable state, and phase handoffs. Execute in the current session using the resource guides; they are methodology, not agent definitions. There is no per-phase model selection.

## Entry and evidence

- Resolve the required Blueprint path, for example `/Game/Blueprints/BP_JumpPad`.
- **`--audit`:** analyze and present the design, save `migration-report.md`, then stop. With `--fast`, use its defaults and report eligibility, but never execute.
- **`--fast`:** eligible simple migrations use the exact 14-task flow below, with one approval gate after the plan. Default goal: Reusability / base class; constraints: none; scope: Everything possible. Evaluate eligibility after technical analysis. If ineligible, explain failed criteria and continue with full-mode design review using the same analysis/defaults; do not re-ask goal questions.
- **`--resume` or an existing plan:** read `docs/migration/blueprint-to-cpp/{BP_Name}/migration-plan.md`. Verify recorded files, migration copy, native class compilation, and `blueprint_hash` against actual progress before offering resume / rewind / restart. Missing outputs for pending tasks are not completed work. Route by `mode`, `phase`, `current_task`, and `failed_task`; retain redesign goal/tier. Fast mode resumes Stage A (analyze/plan), B (execute/verify), or C (swap), not full-mode task numbers.
- Verify external premises against current source/reflection before treating them as facts. Ticket claims and contributor reports are leads, not observations. Ground completion/status claims in actual results.
- `analyze_blueprint_for_migration` supplies the inventory; do not infer an empty component inventory from a general asset-info response. Tool labels below describe capabilities, not guaranteed router command names: resolve the live command/schema before invocation.

## Ownership and completion checks

Before analysis or generation, read the project's `.agents/skills/ripper-blueprint-cpp-principles/SKILL.md` when it exists. Apply its four principles, including current project/Unreal conventions and meaningful naming, during the work and include its evidence-backed checklist in the completion report for every migration mode, including fast mode and "Everything possible". Audits/plans report inspected/planned coverage, not implemented delivery. This is a check within the existing pipeline, not another stage.

If the project has no shared principles skill, use this same four-part report against its agreed C++/Blueprint ownership boundary and the widget rules below:

```markdown
### Blueprint/C++ check

- [ ] Project and Unreal conventions — <Relevant project rules, Unreal patterns, reflected APIs and logical names; evidence or exception.>
- [ ] Correct ownership — <Native functionality/state and Blueprint presentation; evidence or exception.>
- [ ] Editable presentation — <Designer-owned visuals, localized FText references and templates; evidence or exception.>
- [ ] Verified integration — <Applicable references, build/compile, save/reload and affected behavior; evidence or gaps.>
```

Start unchecked; mark [x] only for completed scoped checks supported by actual evidence. Keep missing verification unchecked with its precise gap, and use N/A with a factual reason for genuine exceptions. Bare ticks, a native build alone, and matching display text do not prove Blueprint or localization integration. Do not add tests, runtime runs, or review stages solely to fill the checklist; unmet mandatory acceptance still requires correction or existing authorized disposition.

### Widget migration ownership and naming

For Widget Blueprints, migrate gameplay/state/action decisions and lifecycle to C++; keep designer-owned rendering in the Widget Blueprint. This applies in every mode, including "Everything possible" and fast mode.

- Native owns purchases, eligibility, data selection, subscriptions, entry recycling, and the semantic state (for example, locked or tutorial-active). Blueprint owns how that state looks: sizes, colors, fonts, padding, transforms, styles, animation, and layout. A color or visibility change driven by gameplay is not automatically a reason to hardcode its visual treatment in C++.
- Reuse the existing Designer tree and presentation functions. Send semantic state to a small Blueprint presentation hook where needed. Existing native text/image assignment is appropriate for binding model data; visual templates and display policies must remain editable in Blueprint defaults or existing presentation graphs. Do not introduce a view-model framework just for migration.
- Author widget labels and localized format templates as editable FText in the owning Widget Blueprint Class Defaults, preserving existing String Table IDs/keys and format arguments. C++ chooses labels from semantic state and formats model values; it should not embed designer-owned String Table paths/keys or presentation text in constructors. Keep approved copy/translations in the project's localization source and String Tables, not duplicate Blueprint literals. During migration, serialize defaults against the final native parent, then save/reload and verify typed String Table metadata and rendered labels; matching display text alone is insufficient.
- Before generating BindWidget fields, record old Designer name -> proposed native/Designer name. Follow project naming conventions, with descriptive PascalCase role names such as DescriptionRichTextBlock, UpgradeImage, BuyButton, and BalanceTextBlock. Do not copy placeholder names, numeric suffixes, or prefixes such as DescriptionText_1, Insert_Image_Here, Txt_ButtonText, or WBP_BuyButton into native APIs. Name methods for their actual effects.
- Rename the native field and Designer widget together using Unreal's reference-aware widget rename operation. Preserve graph references, animation targets, delegate/property bindings, focus targets, and references in child/referencing Blueprints. Do not perform raw UObject renames or binary replacements. Do not weaken required bindings to BindWidgetOptional to hide a mismatch.
- Before completion, inspect the C++ diff for presentation literals/setters and the Blueprint for retained styling/animation. Compile all affected widgets, confirm exact binding name/type pairs, and check the real owning screen after recycling/reopening. A native build alone does not prove repaired widget bindings or unchanged presentation.

## Editor lifecycle

Load `cortex-editor` before pipeline start, before each EXECUTE/VERIFY/SWAP phase, and after crash recovery. Require a live editor, healthy MCP connection, and registered `blueprint` domain. Use that skill's reconnect/restart path; never launch, restart, or probe editor lifecycle with ad hoc shell commands. Builds use `cortex-build`.

Track successful orchestrator-triggered restarts in `editor_restarts`; hard stop at 3 and return control to the user. Failed preflight after two attempts offers Retry / Manual / Stop, within that cap. After Manual, wait for confirmation and re-run preflight. After a post-build restart, verify the target native class is registered; crash recovery uses `cortex-editor` with `save=no build=no` and verifies `reflect` as well.

## Eligibility and analysis

Ask goal / constraints / scope one question at a time in full mode (skip with `--fast`). Goals: performance, reusability/base class, complexity management, cleanup/tech debt, or redesign/restructure. Constraints may retain specific BP features or avoid new module dependencies; scope may be everything possible, logic only, selected features, or a recommendation.

Analyze in order: `analyze_blueprint_for_migration`, `get_referencers`, `query_class_hierarchy`, `query_class_context`. Classify functional groups/coupling, public-member dependency impact (SAFE: same name/signature; WARNING: changed signature; BREAKING: no native equivalent), and risk (timelines HIGH, dispatchers MEDIUM, simple events LOW).

Separate semantic decisions from visual treatment. Native owns game rules/state, persistence, collision, simulation and action eligibility; BP retains designer-owned presentation. Do not recommend migrating decorative spatial construction, visual setup, or component configuration merely because scope is "Everything possible". Classify UserConstructionScript: visual-sync stays; approved structural logic translates to `OnConstruction()`, not the constructor. Read `resources/cpp-migration.md` and `resources/cpp-migration-specialist.md` for classification and generation patterns.

### Fast eligibility — all criteria required

| Criterion | Check | Source |
|---|---|---|
| High confidence | `migration_confidence = high` | migration analysis |
| No external dependents | `referencers = 0` | referencer query |
| No child Blueprints | `blueprint_children_count = 0` | migration analysis |
| No timelines | `timelines` empty | migration analysis |
| No event dispatchers | `event_dispatchers` empty | migration analysis |
| No interfaces | `interfaces_implemented` empty | migration analysis |
| Native parent | Parent class path starts `/Script/` | migration analysis |
| No structural ConstructionScript | Only visual-sync UCS nodes | analysis + graph inspection |
| Single pass | All groups migrate in one pass; no HIGH-risk deferrals | group analysis |
| Not redesign | Goal is not redesign/restructure | selected goal |

Classify `complexity: simple` only when the first nine criteria hold, including **zero referencers and zero children**; otherwise `complex`. Fast eligibility additionally excludes redesign. Classification selects verification depth; it does not waive mandatory widget/integration checks.

### Redesign — only when requested

Group responsibilities and inspect existing native overlap before creating classes. Check parent/siblings first; stop the scan if no overlap. Use `query_usages` for relevant member references. Prefer merging into existing owners over duplicate components.

| Tier | Ownership | Constraints |
|---|---|---|
| 1 | Component extraction | Actor-instance-state references force Tier 1. Use SceneComponent for spatial responsibilities, ActorComponent for pure logic. |
| 2 | Subsystem or function library | Truly stateless/shared logic or subsystem-owned state; WorldSubsystem for level scope, GameInstanceSubsystem for persistent state, function library for stateless utilities. |
| 3 | Distinct actor split | Rare, unvalidated advanced route; secondary actor placement/reference updates are manual. |

Prefer the lowest justified tier. Structural UCS logic cannot extract into a component: keep it on the primary actor or in BP. Map every item to its target class. Primary classes preserve Blueprintability; components use appropriate spawnability/class-group specifiers. All generated classes stay in one module.

Integration: owner→component uses a cached `UPROPERTY()` pointer; component→owner uses `GetOwner<T>()` or an interface; notifications use multicast delegates; component→component uses owner mediation or delegates, not direct `FindComponentByClass` coupling. List STAYING nodes needing manual rewiring to migrated variables. Tier-3 secondary-target rows use `Automated: No` and remain annotated in BP until manual work is confirmed.

## Durable artifacts

Use `docs/migration/blueprint-to-cpp/{BP_Name}/`:

| Artifact | Contract |
|---|---|
| `migration-plan.md` | Durable resume source, updated through all phases. |
| `migration-report.md` | Always save the complete analysis recommendation in audit and full/fast planning: outcome/reasons, moves/stays table, integration guide, warnings, timestamp. Report its actual path. |
| `design.md` | Optional for multi-pass, HIGH-risk items, deferred groups needing explanation, or complex dependency chains. |
| `rollback.json` | Finalizer's machine-readable recovery record; schema in `resources/bp-migration-finalizer.md`. |

Generated code stays in the plan until PREPARE, under `### Header ({ClassName}.h)`, `### Source ({ClassName}.cpp)`, and `### Build.cs Changes (if needed)`. Extract by heading, not arbitrary code fence. Only redesigns generating 4+ files may use `generated/`, recording those paths. Do not produce legacy numbered JSON artifacts or separate `report.json`.

### Frontmatter and sections

Preserve these keys (including on resume):

```yaml
blueprint: /Game/Blueprints/BP_Name
target_class: ATargetClass
target_header: Source/Module/TargetClass.h
target_source: Source/Module/TargetClass.cpp
status: planned
current_task: 0
total_tasks: 0
failed_task: null
phase: analyze
created: "<ISO timestamp>"
last_updated: "<ISO timestamp>"
blueprint_hash: "<observed hash>"
migration_pass: 1
total_planned_passes: 1
deferred_groups: []
tasks: []                 # entries: {id, status}; populate during PLAN
files_created: []
files_modified: []
editor_restarts: 0
complexity: simple        # or complex, from analysis
goal: reusability         # performance|reusability|complexity|cleanup|redesign
mode: full                # fast for the 14-task route
redesign_tier: null       # 1|2|3 for redesign
target_classes: []        # entries: {name, type, parent, file_h, file_cpp}
```

Plan sections: `## Pre-Migration Snapshot` (summary plus `### Variables`, `### SCS Components`, `### Graphs`), `## Design Decisions`, `## Migration Scope`, `## Ground Truth Table`, `## Generated C++ Code`, `## Task List`, `## Execution Log` with `### Node Mappings`, `## Verification Results`, `## Final Report`. Snapshot records parent/type/compile state/confidence, nodes/referencers/children, variable types/defaults/exposure/categories/usage, SCS names/classes/roots, and graph event/read/write/component usage.

Redesign adds `## Responsibility Groups`, `## Architecture Proposal`, `## Responsibility Map`, `## Integration Points`, and Tier-3 `## Manual Migration Steps`. Map BP items to target classes, actions, and rewiring notes.

Update sections idempotently: read first, locate the exact heading, replace its section if present or append if absent; update `phase` and `last_updated` in the same edit. Use text anchors, not assumed line numbers. After **every task**, persist `current_task`, task status, timestamp and applicable file/restart records **before** marking the session task complete or starting the next. Fast task IDs in frontmatter are numeric 1–14; `Fast-` labels select the guides' fast task mapping. On failure persist `status: failed` and `failed_task` before presenting recovery choices.

## Ground truth and generation

Before generation, inspect every migrating graph with `graph_list_nodes` and its nodes with `graph_get_node`, always `compact=false`: hidden pins, world context, class references, positions and pin counts matter. Macro graphs, delegate signature graphs and collapsed subgraphs require manual review where these tools cannot reach them.

### Ground Truth Table

| Node ID | Display Name | Type | Function/Property | Target | Parameters | Notes | Target Class | Automated |
|---|---|---|---|---|---|---|---|---|

Use Node ID for tool calls and Display Name for user-facing references. Record exact functions (resolve display names/`K2_` signatures with reflection), casts, variable reads/writes, component-bound events (`AddDynamic`, not a direct call), delegate calls/bindings, and latent treatment. Standard rows target the single native class with `Automated: Yes`; redesign follows its responsibility map.

Generate complete header/source and any Build.cs patch during PLAN. Read defaults from the snapshot; never invent values. Native-created component names match SCS variable names. Preserve applicable `Super::BeginPlay`, `Super::Tick`, and `Super::OnConstruction`; timelines use `UTimelineComponent` with curves set up in BeginPlay; dispatchers use dynamic multicast delegates. Follow project/Epic standards, matching header first in `.cpp`, then engine/project includes. Use forward declarations across generated classes where permitted by UHT; create/attach Tier-1 subobjects in the primary class. Build all generated files together and diagnose compiler errors against their owning file.

Cross-reference every migrating row against its target class's code before plan approval. Missing equivalent = ERROR: correct it before the gate. Parameter differences = documented warning. Extra or substituted behavior = IMPROVEMENT: present separate **Generated C++ — Faithful Translation** and **Optional: Suggested Improvement** versions; faithful is default and improvements require explicit user selection. Node-to-code coverage is semantic, not permission to invent extra calls. Record any generation warnings under `### Code Generation Notes`.

## Pipeline and gates

### ANALYZE → PLAN

Present the snapshot, up to six functional groups/coupling warnings, dependency impact, and explicit MIGRATING / STAYING / DEFERRED items with reasons. Redesign additionally presents class architecture, responsibility map, integration/rewiring needs and adjustable tier; Tier 3 explicitly discloses manual secondary work.

**Audit:** save the recommendation, present design/eligibility, stop without generation or execution. **Full mode:** ask design approval (approve / adjust scope or tier / cancel), then initialize the plan and generate code/tasks. **Eligible fast mode:** combine analysis and planning without a design gate. A partial plan may be checkpointed after code generation before completing tasks.

Each planned task has **Action / Verify / Rollback**. Record `total_tasks`, `tasks`, `phase: plan`, and `status: planned`. Present scope, code preview, risks and task count; resolve faithful-vs-improvement choice before execution. **Plan gate:** approve and execute / review full code / adjust / cancel. Approval sets `status: approved`. Fast mode may switch to the full pipeline at plan review without repeating analysis; review re-presents the gate, cancellation removes the task-owned plan.

### Full-mode task contract

Adapt subtask counts for complexity/multiple file pairs; preserve action ordering and record actual IDs.

| Phase | Tasks |
|---|---|
| PREPARE (inline) | 1 MCP; 2 staleness; 3 Build.cs; 4 duplicate BP; 5 header; 6 source; 7 build; 8 restart through `cortex-editor`, verify native registration. Task 8 transitions `phase: execute`. |
| EXECUTE | 9 collisions; 10 reparent; 11 disconnect migrated events + remove orphan chains; 12 remove functions leaf-first; 13 remove variables reverse-dependency; 14 remove migrated SCS; 15 smoke migrated copy. Follow executor guide, including its pre-reparent collision/data-loss checks. |
| VERIFY | 16 structural verification; 17 dependency impact. Simple inline; complex follows verifier guide. |
| SWAP | 18 disable auto-save; 19 rename swap; 19b remove orphaned nodes; 19c compile then save; 20 fix redirectors/recompile dependents; 21 re-enable auto-save. Follow finalizer guide's exact inter-rename fixup and rollback sequence. |
| COMPLETE | 22 final report + rollback record; verified-backup decision; completion checks. |

Create session tasks per phase with an upcoming-phase summary, not the entire task tree upfront. PREPARE executes directly. Load only the relevant phase guide and plan sections: executor gets frontmatter/snapshot/scope/code/ground truth/task range; verifier gets snapshot/scope/execution log/node mappings; finalizer gets execution log/node mappings/verification/task range. For redesign cleanup, scope code/rows to the target class rather than loading all generated code.

### Exact fast-mode contract

Use this list, not a re-derived compression of the full-mode table:

| Phase / owner | Task | Action |
|---|---|---|
| PREPARE / inline | Fast-1 | Check/update Build.cs automatically; log additions, no pause. |
| PREPARE / inline | Fast-2 | Duplicate Blueprint. |
| PREPARE / inline | Fast-3 | Write C++ header. |
| PREPARE / inline | Fast-4 | Write C++ source. |
| PREPARE / inline | Fast-5 | Build project. |
| PREPARE / inline | Fast-6 | Restart editor, verify class. |
| EXECUTE / executor guide | Fast-7 | Validate collisions; only automatic resolution when unambiguous. |
| EXECUTE / executor guide | Fast-8 | Reparent to C++ class. |
| EXECUTE / executor guide | Fast-9 | Disconnect migrated events + delete orphans. |
| EXECUTE / executor guide | Fast-10 | Remove migrated functions. |
| EXECUTE / executor guide | Fast-11 | Remove migrated variables. |
| EXECUTE / executor guide | Fast-12 | Remove migrated SCS components. |
| VERIFY / orchestrator, not executor | Fast-13 | Inline verification: compile, parent, components, variables, functions, orphans. |
| SWAP / finalizer guide | Fast-14 | Rename swap, orphan cleanup, compile, save, fix redirectors, report/rollback. |

Fast mode has no routine verification approval or backup menu. Passing Fast-13 proceeds to swap. Failure sets `complexity: complex` and offers Fix / Full verify / Stop; Full verify inspects current state without re-executing migration. Skip auto-save disable/re-enable tasks in fast mode; they were not performed. Auto-archive a verified backup to `/Game/Migration/Backups/{BP_Name}_Backup`; if absent, warn that recovery is VCS-only. Report the observed backup outcome, not a fictitious archived path.

### EXECUTE — mutation boundaries

Follow `resources/bp-migration-executor.md`, including collision handling, explicit acknowledgment of reported SCS data losses, compile checks after each removal, and `Automated` filtering for item-level cleanup. Global collision/reparent/verification steps still apply. Do not silently rewire STAYING nodes; report them. After Tier-3 automated work, present Manual Migration Steps and wait for confirmation before VERIFY.

**Approved bounded graph operations** (`replace_entry`, `copy_subgraph`, `move_subgraph`, `prune_island`) use `resources/typed-blueprint-authoring.md`, not generic disconnect/orphan cleanup. Preview, apply with the preview token, and report `apply`/`compile`/`readback`/`save`/`rollback` statuses and durable locators. Keep `save=false` unless the approved plan explicitly authorizes persistence.

Prune uses partition preview → exact approved-set preview → apply with the **second** token. Shared/blocked nodes stay; `complete=false` is incomplete inventory, not approval. The bounded MCP route is complete-or-refuse, including prospective apply size before mutation. `max_scanned_nodes` bounds traversal, not response capacity; `graph.apply_patch` is not paginated for approval and is never nested in `batch_query`. Only lossless large-island inventory remains unsupported ([CortexSandbox #102](https://github.com/etelyatn/CortexSandbox/issues/102)).

If the editor lacks the operation, record editor/plugin identity, leave the asset untouched and return the blocker. Never substitute raw disconnect/orphan deletion, a batch, or `run_python`. After an ambiguous transport/post-apply result, **Stop and reconcile** actual state by readback before any new authorized mutation; never approve partial inventory or blindly resend.

### VERIFY → SWAP → COMPLETE

Simple verification: clean compile, target parent, post-SCS count = snapshot minus migrated components, migrated variables/functions absent, zero orphaned nodes. Zero referencers allows skipping dependency checks; unexpected dependents or inline failures require the full verifier guide. Record that simple verification skips CDO property comparison and requires runtime behavior verification.

Complex verification follows `resources/bp-migration-verifier.md`: inventory/defaults/logic/assets/attachments/dependency impact, multi-class coverage and manual rewiring. Respect its unsafe-tool restriction: do not use `compare_blueprints` on recently reparented state until its cited fix is confirmed deployed; use individual analysis/default reads. Report runtime-only wiring/attachment limitations rather than claiming static proof.

**Full-mode verification gate:** swap / fix / pause / abort. Abort removes only the migration copy and task-created generated files, preserves the original, and records failure. Passing verification is not swap authority until approved. Fast mode follows its already-approved no-extra-gate route.

Follow `resources/bp-migration-finalizer.md` exactly: original→backup, intermediate redirector fixup, copy→original; rollback a failed rename/save and record both error and recovery status. Remove approved orphaned nodes, compile clean **before saving**, verify save success, fix redirectors/recompile dependents, restore auto-save if disabled. Verify backup persistence and write `rollback.json` plus `## Final Report`.

Full mode offers keep / archive / delete only when `backup_verified: true`. Archive uses rename plus source-directory redirector fixup. If backup is absent, skip the menu and explicitly warn that recovery requires VCS; never claim the original is preserved. Fast mode auto-archives only a verified backup. Finish with actual native/Blueprint/artifact paths, deferred groups/next-pass restart needs, applicable ownership checklist and precise unverified integration gaps; set `status: completed`, `phase: complete` only on successful completion.

## Failure and crash recovery

Persist failure state first, then offer fix / skip / stop; skip only independent non-required work, not a safety gate. Fix updates both implementation and plan before retrying. Connection errors stop the phase immediately; no blind retries or tool workarounds. Recover through `cortex-editor` within the restart cap.

Before resuming an interrupted task, reconcile its actual preconditions: EXECUTE checks migration-copy integrity; SWAP checks completed renames and referencer targets; read-only VERIFY can retry after editor recovery. Never replay a saved `failed_task` blindly after a partial swap. Reverify post-build class registration, update timestamps, and resume only the remaining task range.

## Supported types and references

Actor (native base/subclass), Widget (UUserWidget + BindWidget), Component (ActorComponent/SceneComponent), FunctionLibrary (static functions), Interface (UInterface/IInterface pair).

- Classification/code patterns: `resources/cpp-migration.md`, `resources/cpp-migration-specialist.md`.
- Phase protocols: `resources/bp-migration-executor.md`, `resources/bp-migration-verifier.md`, `resources/bp-migration-finalizer.md`.
- Guarded graph contract: `resources/typed-blueprint-authoring.md`.
- Project standards/design history: `docs/unreal-coding-standards.md`, `docs/plans/2026-02-27-bp-migration-pipeline-design.md`, `docs/plans/2026-02-26-bp-migration-v5-design.md`.
