---
name: cortex-bp-migrate
description: Blueprint-to-C++ migration pipeline with conversational analysis, plan-driven execution, visual progress tracking, and hard gates. Supports --audit, --resume, and --fast (streamlined mode for simple migrations).
---

# Blueprint to C++ Migration Pipeline

Migrate a Blueprint to C++ using either:
- Full mode (default): 4-stage pipeline, ANALYZE → PLAN → EXECUTE → COMPLETE, with hard gates
- Fast mode (`--fast`): 3-stage streamlined flow with a single approval gate for eligible simple migrations

## Entry Point

Parse user input for:
- **Blueprint path** (required) — e.g., `BP_JumpPad` or `/Game/Blueprints/BP_JumpPad`
- **`--audit`** — run ANALYZE stage only, present design without executing. If combined with `--fast`, run analysis with auto-defaults and report fast mode eligibility, but stop after presenting the design (do not execute).
- **`--resume`** — detect and resume from saved migration state. If the plan's frontmatter contains `mode: fast`, resume within the Fast Mode Pipeline (route to Stage A/B/C based on `phase` and `current_task`).
- **`--fast`** — streamlined mode for simple migrations (1 gate instead of 4, fewer agent dispatches). Auto-detected eligibility; falls back to full pipeline if criteria not met.

## Fast Mode Eligibility

When `--fast` is specified, the pipeline checks eligibility AFTER the technical analysis (ANALYZE Step 2) completes. Eligibility cannot be checked before analysis because the criteria depend on analysis results.

**All criteria must be true:**

| Criterion | Check | Source |
|-----------|-------|--------|
| High confidence | `migration_confidence` = "high" | `analyze_blueprint_for_migration` |
| No external dependents | `referencers` = 0 | `get_referencers` |
| No child Blueprints | `blueprint_children_count` = 0 | `analyze_blueprint_for_migration` |
| No timelines | `timelines` array is empty | `analyze_blueprint_for_migration` |
| No event dispatchers | `event_dispatchers` array is empty | `analyze_blueprint_for_migration` |
| No interfaces | `interfaces_implemented` array is empty | `analyze_blueprint_for_migration` |
| C++ parent class | Parent class path starts with `/Script/` (not `/Game/`) | `analyze_blueprint_for_migration` |
| No structural ConstructionScript | UserConstructionScript contains only visual-sync nodes (no structural logic) | `analyze_blueprint_for_migration` + graph inspection |
| Single pass | All functional groups migrate in one pass (no HIGH-risk items requiring deferral) | Derived from functional group analysis |
| Not redesign goal | Goal is not "Redesign/restructure" | User-selected goal (or auto-selected by --fast) |

**If eligible:** Proceed with fast mode flow (see Fast Mode Pipeline below).

**If not eligible:** Report which criteria failed and fall back to full pipeline:
```
Fast mode not available for {BP_Name}:
  ✗ Has 3 referencers (fast mode requires 0)
  ✗ Implements IInteractable interface

Falling back to full pipeline (4-stage with gates).
```
The full pipeline continues from where fast mode left off — the analysis data is already collected, so ANALYZE Step 2 results are reused. The pipeline enters ANALYZE Step 3 (present design) directly using the auto-selected defaults (Goal: "Reusability / base class", Constraints: "No constraints", Scope: "Everything possible"). Do NOT re-ask goal questions — the user chose `--fast`, which implies these defaults.

## Resume Detection

If `--resume` flag OR `docs/migration/blueprint-to-cpp/{BP_Name}/migration-plan.md` exists:

1. Read `migration-plan.md` YAML frontmatter
2. Parse: `status`, `current_task`, `failed_task`, `phase`, `blueprint_hash`, `mode`, `goal`, `redesign_tier`
3. **Route by mode:** If frontmatter contains `mode: fast`, resume within the Fast Mode Pipeline. Route to Stage A (if `phase: analyze` or `phase: plan`), Stage B (if `phase: execute`), or Stage C (if `phase: swap`) based on `phase` and `current_task`. If `mode` is absent or not `fast`, resume in the full pipeline.
4. **Route by goal:** If frontmatter contains `goal: redesign`, use redesign-aware analysis path in ANALYZE (extended presentation, tier classification, responsibility groups).
5. Verify workspace state:
   - Do files in `files_created` actually exist on disk?
   - Does `BP_Name_Migration` copy exist in the editor?
   - Does the C++ class exist and compile?
   - Does `blueprint_hash` match current Blueprint? (staleness check)
6. Present resume point to user with options: [resume / rewind / restart]
7. On resume: create TaskCreate entries for remaining tasks, continue from saved phase

## Pre-Flight Check (Task 0)

Before entering any stage, verify the editor is alive and MCP is healthy.

**Steps:**
1. Use the Skill tool: `skill: "cortex-editor"` — checks the editor process, port file, MCP connection, and restart path when needed
   - If all checks pass AND `blueprint` domain is registered -> proceed to ANALYZE
   - If editor not running OR port file stale -> go to step 2
   - If MCP connection fails but editor is running -> go to step 3
   - If `blueprint` domain is missing -> invoke `/cortex-editor` again and use its restart path, then re-run `/cortex-editor`

2. **Editor not running:** Use the Skill tool: `skill: "cortex-editor"` to start the editor
   - The skill handles: engine path lookup, background launch with `-AutoDeclinePackageRecovery`, port file polling (120s timeout), MCP verification
   - After skill completes -> re-run `/cortex-editor` to confirm `blueprint` domain is registered

3. **MCP connection failed (editor running):** Use the Skill tool: `skill: "cortex-editor"`
   - `/cortex-editor` retries `get_status` and can escalate from reconnect diagnostics to a full restart path when the editor process is healthy but the MCP client lost its connection.
   - If reconnect fails -> keep the workflow inside `/cortex-editor` and use its restart path

**This check runs:**
- At pipeline start (before ANALYZE)
- Before each phase agent dispatch (before EXECUTE, VERIFY, SWAP)
- After any editor crash recovery

**On failure after 2 retries (respecting pipeline-wide restart cap of 3):** Present to user via AskUserQuestion:
```
Editor could not be started. Options:
[1] Retry — try starting editor again
[2] Manual — I'll start it myself, then continue
[3] Stop — abort migration
```
If user picks [2] Manual: wait for user to confirm editor is ready, then run `/cortex-editor` to verify MCP connection and `blueprint` domain before proceeding.

**Note:** Do NOT use inline bash commands (`tasklist`, `grep`, port file globbing) for editor lifecycle operations. Always delegate to the Cortex core skills which handle edge cases (stale port files, PID validation, multiple editor instances) consistently.

**Never launch or restart the editor with raw bash commands** (e.g., `start "" "$ENGINE_PATH/..."` or `UnrealEditor.exe &`). Use the Skill tool with `cortex-editor` instead. Raw launch bypasses graceful shutdown, port file management, and MCP verification.

### Pipeline-Wide Restart Limit

Track editor restarts in frontmatter field `editor_restarts`.

- Hard cap: `3` total restarts across the full migration pipeline
- Increment after every successful orchestrator-triggered restart through `/cortex-editor`
- If `editor_restarts >= 3`: stop immediately and present:
  ```
  Editor has restarted 3 times in this migration.
  This usually indicates an underlying engine/plugin issue.
  Please investigate manually (logs, crash report, plugin state), then resume with --resume.
  ```

### Pre-Dispatch Protocol (referenced by all phase dispatches)

Before dispatching ANY phase agent (executor, verifier, finalizer):
1. Run `/cortex-editor` — verify editor alive + MCP connected + `blueprint` domain registered
2. If editor is down or wedged -> use `/cortex-editor`
3. Only dispatch agent once MCP connection is confirmed and `blueprint` domain is registered
4. If editor cannot be started after 2 attempts (respecting pipeline-wide restart cap) -> present:
   ```
   Editor is down before agent dispatch. Options:
   [1] Retry — try starting editor again
   [2] Manual — I'll start it myself, then continue
   [3] Stop — save progress, resume later with --resume
   ```
   If user picks [2] Manual: wait for confirmation, re-run `/cortex-editor` before dispatching.

This prevents wasted agent dispatches (significant overhead per dispatch) when the editor is already dead.

### Model Selection Rules

**All migration phase agents MUST use sonnet or higher.** Do not dispatch with haiku.

**Intent:** `model: sonnet` is set as a **capability floor** — these agents require at least sonnet-level reasoning for MCP tool calls. This is an intentional trade-off:
- If your session runs on Opus, agents will run at sonnet (not Opus). This is by design for cost control — phase agents are mechanical executors, not creative thinkers. Sonnet is sufficient for MCP operations.
- If your session runs on sonnet, agents inherit the same level (no change).
- If your session runs on haiku, agents are upgraded to sonnet (the whole point).

| Context | Model | Reason |
|---------|-------|--------|
| Phase agents (executor, verifier, finalizer) | sonnet (frontmatter enforced) | MCP tool calls require understanding tool naming, parameter schemas, and error handling |
| Orchestrator operations | session model (no override) | Orchestrator runs at whatever model the user's session uses; do not attempt to switch models mid-conversation |
| Error recovery, MCP response interpretation | sonnet (via agent dispatch) | Complex reasoning required |

The phase agent frontmatters enforce `model: sonnet`. Do not override this with `model: haiku` in the Task tool dispatch.

**Why not haiku for MCP tasks:** During the BP_JumpPad migration, haiku agents confused TCP command names with MCP tool names, returned "UNKNOWN_COMMAND" errors, and couldn't distinguish "editor not running" from "stale port file." Sonnet handled all of these correctly.

## Implementation Notes

### Content Anchors

When this skill references a location, use unique text anchors rather than line numbers.

### Append Mechanism (Idempotent)

When this skill says "append to migration-plan.md":
1. Read `migration-plan.md` first.
2. Locate the target `##` heading.
3. If the heading exists, replace that entire section (until the next `##` heading).
4. If the heading does not exist, insert the new section at the end.
5. Update frontmatter `phase` and `last_updated` in the same edit.

### Agent Context Scoping

Before dispatching an agent, extract and send only relevant sections:

| Agent | Receives |
|-------|----------|
| Executor | Frontmatter + Pre-Migration Snapshot + Migration Scope + Generated C++ Code + Task List (tasks in range only) |
| Verifier | Frontmatter + Pre-Migration Snapshot + Migration Scope + Execution Log + Node Mappings |
| Finalizer | Frontmatter + Execution Log + Node Mappings + Verification Results + Task List (tasks in range only) |

### Artifact Rules

Each migration produces at most 3 files:
- `migration-plan.md` — primary document, updated through all stages
- `design.md` — optional, complex migrations only
- `rollback.json` — machine-readable rollback state

Do NOT write legacy artifacts:
- `01-pre-migration.json`
- `02-migration-plan.json`
- `generated/*.h`
- `generated/*.cpp`
- `03-node-mapping.json`
- `04-verification.json`
- `05-rollback.json`
- `report.json`

## Fast Mode Pipeline

> **ROUTING:** If `--fast` was NOT specified, skip this entire section and proceed directly to **Stage 1: ANALYZE**.

**Applies when:** `--fast` flag is set AND eligibility check passes.

**Key differences from full pipeline:**
- 3 stages instead of 4 (ANALYZE+PLAN combined, EXECUTE+VERIFY combined, SWAP+COMPLETE combined)
- 1 approval gate instead of 4 (after plan generation, before execution)
- No goal questions (auto-select "Reusability / base class")
- No separate design approval gate
- Inline verification only (no verifier agent dispatch)
- Auto-archive backup after successful swap
- 2 agent dispatches total (executor + finalizer)

**Fast mode flow:**

```
Stage A: ANALYZE + PLAN (no gate between them)
  └─ ONE approval gate ──────────────────────────
Stage B: EXECUTE + VERIFY (inline verification)
Stage C: SWAP + COMPLETE (auto-cleanup)
```

### Stage A: Analyze and Plan (Combined)

**Step A1: Pre-Flight Check**
Run Pre-Flight Check (Task 0) — same as full pipeline. Editor must be alive.

**Step A2: Technical Analysis (No Goal Questions)**
Skip the 3 conversational goal questions. Auto-select defaults:
- Goal: "Reusability / base class"
- Constraints: "No constraints"
- Scope: "Everything possible"

Call MCP tools (same as full pipeline ANALYZE Step 2):
1. `analyze_blueprint_for_migration`
2. `get_referencers`
3. `query_class_hierarchy`
4. `query_class_context`

**Step A3: Eligibility Gate**
Check fast mode eligibility criteria (from section above).
If not eligible -> fall back to full pipeline at ANALYZE Step 3.

**Step A4: Graph Node Inspection**
Call `graph_list_nodes` with `compact=false` on each migrating graph, then `graph_get_node` with `compact=false` on every node to capture pin values, connections, and logic. Build the Ground Truth Table mapping each BP node to its C++ equivalent. This step is NOT skipped in fast mode because it's critical for code accuracy.

**`compact=false` is REQUIRED** — the default `compact=true` strips hidden pins (world-context, self, class-reference) and position data that the migration Ground Truth Table depends on. Missing hidden pins means missing world-context arguments in generated C++ latent function calls.

(Full protocol: see PLAN Step 1. Key sub-steps: list all nodes per graph, inspect each node's pins/connections/defaults, build BP-node-to-C++-equivalent mapping table.)

**Step A5: Generate C++ Code**
Generate the C++ header and source files using the analysis results and Ground Truth Table. Apply all code generation rules (naming, includes, UPROPERTY/UFUNCTION macros, component initialization). Cross-reference every generated line against the Ground Truth Table.
(Full protocol: see PLAN Step 2 and Step 2.5. Key sub-steps: generate header with UPROPERTY/UFUNCTION declarations, generate source with component creation and function bodies, cross-reference every line against Ground Truth Table.)

**Checkpoint after A5:** At this point you have: analysis results, eligibility confirmed, Ground Truth Table, and generated C++ code. If your context is getting large, write `migration-plan.md` NOW (partial — snapshot + scope + ground truth + code) before generating the task list in A6. Complete the remaining sections in A7.

**Step A6: Generate Compressed Task List**
Fast mode uses a compressed task list. Tasks that are skipped or combined:

| Full Pipeline Task | Fast Mode | Reason |
|-------------------|-----------|--------|
| Task 1: Verify MCP | Keep (already done in A1) | — |
| Task 2: Staleness check | **Skip** | We just analyzed it |
| Task 3: Build.cs check | **Check only** (no pause on success) | Auto-add modules if needed |
| Task 4: Duplicate Blueprint | Keep | Required |
| Task 5-6: Write C++ | Keep | Required |
| Task 7: Build | Keep | Required |
| Task 8: Restart editor | Keep (automated) | Required |
| Task 9: Collision check | **Check only** (no pause on success) | Auto-resolve if possible |
| Task 10: Reparent | Keep | Required |
| Task 11: Disconnect events | Keep | Required |
| Task 11b: Delete orphans | Keep | Required |
| Task 12-14: Remove funcs/vars/components | Keep | Required |
| Task 15: Smoke test | **Merge with verify** | Combined in Stage B |
| Task 16: Structural verify | **Inline** (compile + parent + count) | No verifier agent |
| Task 17: Dependency check | **Skip** | referencers = 0 (known) |
| Task 18: Disable auto-save | **Skip** | No dependents to corrupt |
| Task 19: Rename swap | Keep | Required |
| Task 20: Fix redirectors | Keep | Required |
| Task 21: Re-enable auto-save | **Skip** | Was never disabled |
| Task 22: Final report | Keep (simplified) | Required |

**Use the following 14-task list exactly as written.** The mapping table above is for reference only — do not re-derive the task list from the mapping.

**Effective fast mode task list (14 tasks):**

```
── PREPARE ──────────────────────────────────
Fast-1: Check/update Build.cs (auto, no pause)
Fast-2: Duplicate Blueprint
Fast-3: Write C++ header
Fast-4: Write C++ source
Fast-5: Build project
Fast-6: Restart editor, verify class

── EXECUTE ──────────────────────────────────
Fast-7: Validate collisions (auto, no pause)
Fast-8: Reparent to C++ class
Fast-9: Disconnect events + delete orphans
Fast-10: Remove migrated functions
Fast-11: Remove migrated variables
Fast-12: Remove migrated SCS components

── VERIFY (orchestrator, not executor) ─────
Fast-13: Inline verification (compile + parent + components)

── SWAP ─────────────────────────────────────
Fast-14: Rename swap + delete orphaned nodes + save + fix redirectors + report
```

**Step A7: Write Plan Document**
Write `migration-plan.md` with all sections (same artifact model as full pipeline — Phase 3 single-document format). Include:
- YAML frontmatter with `mode: fast`, `complexity: simple`, compressed task list
- Pre-migration snapshot (inline)
- Design decisions (auto-generated, no user input)
- Generated C++ code (inline)
- Compressed task list

**Step A8: ONE Approval Gate**
Present the complete plan summary to the user:

```
Fast Migration: {BP_Name} → {ClassName}

  Confidence: HIGH
  Referencers: 0
  Components: {N} ({M} migrating, {K} staying)
  Graphs: {N} ({events} events migrating)
  Tasks: 14 (compressed from 22)
  Estimated: ~5-8 minutes

  Migrating:
    Variables: {list}
    Functions: {list}
    Components: {list}
  Staying in BP: {list or "nothing"}

  C++ class preview:
    {ClassName} : {ParentClass}
    Components: {list}
    Overrides: {list}

  [Approve]       — execute all tasks automatically
  [Review]        — show full C++ code before approving
  [Full Pipeline] — switch to full 4-stage pipeline with gates
  [Cancel]        — abort migration
```

**If IMPROVEMENTs were flagged in Step A5:** Add an additional option to the gate:
- [Review improvements] — show faithful vs. improved code, choose which to use

Present the faithful/improvement binary choice (same format as full pipeline Step 5) before executing. The faithful version is always the default.

- **[Approve]:** Proceed to Stage B. Update frontmatter: `status: approved`.
- **[Review]:** Show full generated C++ code. Then re-present the gate.
- **[Full Pipeline]:** Fall back to full pipeline at PLAN Step 4 (plan approval gate). The plan document already exists, so the full pipeline picks up from the plan review.
- **[Cancel]:** Abort. Clean up plan document.

### Stage B: Execute and Verify (Combined)

**Step B1: PREPARE tasks (orchestrator inline)**
Handle Fast-1 through Fast-6 directly. Same as full pipeline PREPARE but:
- Fast-1 (Build.cs): auto-add modules, don't pause for approval. If modules need adding, add them and log it.
- Fast-6 (restart): automated via `/cortex-editor` (same as Phase 2)
- Update frontmatter after each task (same as Phase 2 Task 4). Use numeric IDs (1-14) in `current_task` regardless of mode — the `mode: fast` field distinguishes fast from full pipeline.

**Step B2: Pre-dispatch** Run Pre-Dispatch Protocol.

**Step B3: Dispatch executor agent** (`cortex-toolkit:bp-migration-executor`, model: sonnet) with:
- Full text of migration-plan.md
- Task range: Fast-7 through Fast-12 (EXECUTE tasks only)

**EXECUTE tasks (executor agent):**
The executor handles Fast-7 through Fast-12. Same cleanup order as full mode:
1. Validate collisions (auto-resolve: if C++ component name matches SCS name, that's expected — skip)
2. Reparent
3. Disconnect events + delete orphaned nodes (combined into one task)
4. Remove functions
5. Remove variables
6. Remove SCS components

**Step B4: Inline verification (orchestrator, no verifier agent)**
After executor completes, orchestrator runs Fast-13 inline:
1. Compile `BP_Name_Migration` -> must compile clean
2. Verify parent class is the target C++ class
3. Compare component count against pre-migration snapshot
4. Verify migrated variables are gone
5. Verify migrated functions are gone
6. Check orphaned node count = 0

**NO verification gate in fast mode.** If all checks pass -> proceed directly to Stage C.

**If any check fails:** Update frontmatter `complexity: complex` (prevents circular routing back to inline verification), then stop and present:
```
Fast mode verification failed:
  ✗ {check}: {details}

Options:
[1] Fix — investigate and retry
[2] Full verify — dispatch verifier agent on current state (does NOT re-execute migration)
[3] Stop — save progress, resume later
```

### Stage C: Swap and Complete (Combined)

**Pre-dispatch:** Run Pre-Dispatch Protocol.

**Dispatch finalizer agent** (`cortex-toolkit:bp-migration-finalizer`, model: sonnet) with:
- Full text of migration-plan.md
- Task range: Fast-14

The finalizer handles in one task:
1. Rename swap (`BP_Name` → `BP_Name_Backup`, `BP_Name_Migration` → `BP_Name`)
2. Fix redirectors + recompile dependents (should be 0 dependents, but run anyway for safety)
3. Verify backup exists on disk
4. Append final report section to migration-plan.md
5. Write rollback.json

**Auto-cleanup (no backup menu in fast mode):**
After finalizer completes:
- If `backup_verified: true` -> auto-archive the backup to `/Game/Migration/Backups/{BP_Name}_Backup` (moved out of content browser sight, but recoverable without git)
- If `backup_verified: false` -> log explicit warning: "WARNING: No backup was created during swap. The original Blueprint cannot be recovered except via git."
- Report: "Backup auto-archived to /Game/Migration/Backups/ (fast mode). Delete manually when confident, or use git to recover if needed."

**Final output:**
```
Fast Migration Complete: {BP_Name} → {ClassName}

  Duration: {time}
  Tasks: 14/14 completed
  C++ class: {ClassName} ({header_path})
  Blueprint: /Game/.../{BP_Name} (reparented)
  Backup: auto-archived to /Game/Migration/Backups/

  Plan: docs/migration/blueprint-to-cpp/{BP_Name}/migration-plan.md
```

Update frontmatter: `status: completed`, `phase: complete`.

## Stage 1: ANALYZE

**Goal:** Understand user goals, analyze the Blueprint technically, present a migration design for approval.

### Step 1: Ask Goal Questions (Conversational — Before Any MCP Calls)

Use `AskUserQuestion` to ask one question at a time:

1. "Why are you migrating this Blueprint?" — options: Performance, Reusability/base class, Complexity management, Cleanup/tech debt, Redesign/restructure
2. "Any constraints for this migration?" — options: Keep specific things in BP, Avoid adding module dependencies, No constraints
3. "What scope are you thinking?" — options: Everything possible, Logic only (keep visual BP), Specific features (I'll choose), Not sure (recommend for me)

### Logic vs Cosmetic Check

Before recommending what to migrate, classify each element by intent — does game logic depend on the value?

**Moves to C++ (logic-driven):** Any operation where the value affects game state or other logic depends on it. Even SetVisibility or SetLocation, if logic controls it (e.g., hiding during state change, positioning based on game rules).

**Stays in BP (purely cosmetic):** Operations where NO other logic reads or reacts to the value — decorative colors, visual-only material swaps, spatial construction for decorative geometry (door frames, wall segments where no gameplay depends on positions).

See `cpp-migration.md` "Logic vs Cosmetic" section for the full classification.

### Step 2: Run Blueprint Analysis (Technical — Via MCP Tools)

Call these MCP tools in sequence:
1. `analyze_blueprint_for_migration` — full Blueprint snapshot
2. `get_referencers` — dependency scan (children, level placements, external callers)
3. `query_class_hierarchy` — parent class chain
4. `query_class_context` — existing C++ in project

From the results:
- Compute functional groups and coupling matrix (see V5 design doc Section 3)
- Classify risk: timelines = HIGH, event dispatchers = MEDIUM, simple events = LOW
- Classify UserConstructionScript nodes: visual_sync stays in BP, structural moves to C++ (see cpp-migration.md resource, "Visual Sync Classification")
- Build SAFE/WARNING/BREAKING dependency impact table

#### Redesign Analysis (When Goal = "Redesign/restructure")

When the user selects "Redesign/restructure" as the migration goal, perform additional analysis after the standard MCP tools:

1. **Responsibility detection** — group BP functions, variables, and components by logical responsibility. Use functional group analysis from coupling matrix. Name each group by its domain (for example, "Health Management", "Movement", "Combat", "UI Binding"). A responsibility = a cohesive set of variables + the functions that read/write them + the components they reference.
2. **Existing C++ integration scan** — use `query_class_context` results to identify existing C++ classes that overlap with detected responsibilities. Also call `query_usages` on key BP functions/variables to find cross-references. Flag merge opportunities where BP logic duplicates existing C++ functionality. **Early exit:** if no overlap found after checking BP parent class and its siblings in the hierarchy, skip further scanning. Do not exhaustively search the entire project.
3. **Tier classification** — classify the migration using these rules:

   **Default hierarchy:** Tier 1 > Tier 2 > Tier 3. Always prefer the lower tier.

   - **Tier 1 (Component extraction):** Responsibilities map to self-contained components. *Indicators:* groups have clear data ownership, minimal cross-group variable access, groups map to standard component patterns.
     - Use `USceneComponent` (or subclass) if the responsibility involves spatial data (transforms, attachment, collision)
     - Use `UActorComponent` if the responsibility is pure logic with no spatial meaning
   - **Tier 2 (Subsystem/utility extraction):** Logic is stateless or shared across multiple actors. *Indicators:* functions don't reference `this` actor's instance state, logic is called from multiple BPs, utility/helper pattern.
     - `UWorldSubsystem` — state scoped to current level, destroyed on level transition
     - `UGameInstanceSubsystem` — state persists across level transitions
     - `UBlueprintFunctionLibrary` — purely stateless utility functions
   - **Tier 3 (True actor split):** BP genuinely represents multiple distinct game entities. *Indicators:* responsibility groups have no shared state, different groups are placed/referenced independently, groups represent different actor archetypes. **Tier 3 is rare — default to Tier 1 unless strong evidence of distinct entities. Tier 3 is specified but unvalidated.**

   **Tiebreaker: actor-state reference = Tier 1.** If a responsibility group references actor instance state (member variables, components), it is Tier 1 regardless of how many BPs share the pattern. Tier 2 is reserved for truly stateless logic or logic whose state lives in a subsystem.

   **Construction script exclusion:** If a responsibility group contains UserConstructionScript nodes with structural logic, it cannot extract to a component (only actors have UserConstructionScript). These nodes must stay on the primary class or remain in BP.

   **Existing C++ merge detection:** Before generating new component/subsystem classes, check if the project already has a matching C++ class (for example, an existing `UHealthComponent`). Use `query_class_hierarchy` under `UActorComponent` and `query_class_context`. If found, propose merging into the existing class rather than generating a duplicate.

4. **Target class mapping** — for each responsibility group, assign a target C++ class:
   - Class name following Unreal conventions (Components: `U{Responsibility}Component`, Subsystems: `U{Name}Subsystem`, Secondary actors: `A{Name}`)
   - Parent class (`UActorComponent` vs `USceneComponent` for Tier 1; subsystem type for Tier 2)
   - UCLASS specifiers: primary class gets `Blueprintable` if source BP was; components get `BlueprintSpawnableComponent` if addable in BP editors; internal-only components get `ClassGroup=(Custom)`
5. **Serialize responsibility groups** — write a `## Responsibility Groups` section to migration-plan.md with named groups and their member items (variables, functions, components). This is the concrete input for the cpp-migration-specialist agent's redesign validation/refinement during PLAN.

### Step 3: Present Migration Design

Synthesize user goals (Step 1) with technical analysis (Step 2). Present:

1. **Blueprint summary** — components, variables, functions, complexity, parent class
2. **Functional groups** with coupling warnings (max 6 groups; merge small ones)
3. **Dependency impact table** — SAFE/WARNING/BREAKING per public member
4. **Scope recommendation** — based on user's stated goals. **Apply anti-over-engineering filter:** do NOT recommend migrating spatial construction, visual setup, or component configuration — these stay in BP regardless of scope setting. See "Anti-Over-Engineering Rule" in the cpp-migration-specialist agent and "When NOT to Migrate" in cpp-migration.md.
5. **MIGRATING / STAYING / DEFERRED columns** — what moves to C++, what stays in BP, what's deferred. The STAYING column must explicitly list items kept in BP with reasons (not just "everything else").

#### Extended Presentation (When Goal = "Redesign/restructure")

When goal is "Redesign/restructure", the design presentation adds these sections after the standard content:

6. **Architecture proposal** — describe the target class structure:
   - Primary class name, parent, and UCLASS specifiers
   - Extracted classes (components, subsystems, or secondary actors) with their types and parents
   - Rationale for each extraction (why this responsibility is a separate class)
   - Tier classification with justification
7. **Responsibility map** — which BP items go to which target class:

   | Item | Target Class | Type | Action |
   |------|-------------|------|--------|
   | MaxHealth, CurrentHealth | UHealthComponent | Component (Tier 1) | MIGRATING |
   | TakeDamage(), OnHealthChanged | UHealthComponent | Component (Tier 1) | MIGRATING |
   | MovementSpeed, JumpForce | AMyCharacterBase | Primary | MIGRATING |
   | BeginPlay, Tick | AMyCharacterBase | Primary | MIGRATING |
   | Widget reference | BP | -- | STAYING |

8. **Integration points** — how extracted classes communicate, using this decision table:

   | Pattern | When to Use |
   |---------|------------|
   | Cached `UPROPERTY()` pointer | Owner -> Component (primary class holds component pointers set in constructor) |
   | `GetOwner<T>()` | Component -> Owner (tightly coupled, single owner type) |
   | `IInterface` + `Execute_*()` | Component -> Owner (reusable component, multiple possible owner types) |
   | `DECLARE_DYNAMIC_MULTICAST_DELEGATE` | One-to-many notification, decoupled (for example, OnHealthChanged) |
   | Owner mediation | Component -> Component (A calls owner, owner calls B) |
   | `UInterface` | Cross-actor communication (Tier 3) |

   **Anti-pattern:** avoid `GetComponentByClass<>()` for frequently-accessed components from the owner — use cached `UPROPERTY()` pointer set in constructor instead. Reserve `GetComponentByClass` for external/cross-actor lookups only.

   **Component-to-component:** recommend pattern 1 (owner mediation) or 2 (delegates). Explicitly discourage direct `GetOwner()->FindComponentByClass<OtherComp>()` which couples components to each other.

9. **Variable reference analysis** — identify STAYING BP nodes that reference MIGRATING variables. These nodes will need rewiring to access data via component (for example, `HealthComp->MaxHealth` instead of `MaxHealth`). List them explicitly as "requires rewiring after migration."
10. **Tier classification** — present as adjustable: "This is classified as Tier {N} ({description}). Is this the right decomposition, or should any of these be split differently?"
11. **For Tier 3 only: Manual migration steps** — list steps requiring human judgment. Add warning: "Tier 3 (true actor split) is an advanced migration pattern. The automated portion handles C++ generation and primary class reparent. All secondary actor placement and reference updates are manual. Proceed?"

### Step 4: Hard Gate — User Approves Design

Present the migration design and ask for approval using `AskUserQuestion`:
- [Approve] — proceed to PLAN stage
- [Adjust scope] — user modifies scope, moves items between MIGRATING/STAYING/DEFERRED columns
- [Adjust tier] — user changes tier classification or target class assignments (redesign only)
- [Cancel] — abort migration

On approval, write `docs/migration/blueprint-to-cpp/{BP_Name}/migration-plan.md` with initial content:

~~~markdown
---
blueprint: /Game/.../{BP_Name}
target_class: {ClassName}
target_header: Source/{Module}/{ClassName}.h
target_source: Source/{Module}/{ClassName}.cpp
status: planned
current_task: 0
total_tasks: 0          # Updated in PLAN stage
failed_task: null
phase: analyze
created: "{ISO timestamp}"
last_updated: "{ISO timestamp}"
blueprint_hash: {hash}
migration_pass: 1
total_planned_passes: 1
deferred_groups: []
tasks: []               # Populated in PLAN stage
files_created: []
files_modified: []
editor_restarts: 0
complexity: {simple or complex}  # From Migration Complexity Classification
goal: {performance|reusability|complexity|cleanup|redesign}
redesign_tier: null       # Set to 1, 2, or 3 when goal is "redesign"
target_classes: []        # List of {name, type, parent, file_h, file_cpp} for multi-class output
---

# {BP_Name} -> {ClassName} Migration

## Pre-Migration Snapshot

| Field | Value |
|-------|-------|
| Blueprint | `/Game/.../{BP_Name}` |
| Parent Class | `{parent}` |
| Type | `{type}` |
| Compiled | `{yes/no}` |
| Total Nodes | `{N}` |
| Migration Confidence | `{high/medium/low}` |
| Referencers | `{N}` |
| Children | `{N}` |

### Variables

| Name | Type | Default | Exposed | Category | Usage Count |
|------|------|---------|---------|----------|-------------|
| ... |

### SCS Components

| Name | Class | Is Root |
|------|-------|---------|
| ... |

### Graphs

| Name | Nodes | Events | Variables Read | Variables Written | Components Referenced |
|------|-------|--------|----------------|-------------------|----------------------|
| ... |

## Design Decisions

- {3-5 bullets from ANALYZE synthesis}

## Migration Scope

| Migrating to C++ | Staying in Blueprint | Deferred |
|-------------------|---------------------|----------|
| ... | ... | ... |

<!-- When goal = "redesign" — add these sections -->

## Responsibility Groups

| Group Name | Variables | Functions | Components | Target Class |
|-----------|-----------|-----------|------------|-------------|
| {name} | {list} | {list} | {list} | {TargetClass} |
| ... | ... | ... | ... | ... |

## Architecture Proposal

**Tier:** {1: Component extraction | 2: Subsystem extraction | 3: Actor split}

**Target Classes:**

| Class | Type | Parent | UCLASS Specifiers | Purpose |
|-------|------|--------|-------------------|---------|
| {PrimaryClass} | Primary | {BP parent} | Blueprintable | Main actor identity |
| {ComponentClass} | Component | UActorComponent/USceneComponent | BlueprintSpawnableComponent | {responsibility} |
| ... | ... | ... | ... | ... |

## Responsibility Map

| BP Item | Target Class | Action | Notes |
|---------|-------------|--------|-------|
| {var/func/component} | {TargetClass} | MIGRATING / STAYING | {rewiring needed?} |
| ... | ... | ... | ... |

## Integration Points

| From | To | Pattern | Detail |
|------|-----|---------|--------|
| {PrimaryClass} | {ComponentClass} | Cached UPROPERTY | `UPROPERTY() UHealthComponent* HealthComp` |
| {ComponentClass} | {PrimaryClass} | GetOwner<T> | `GetOwner<APrimaryClass>()` |
| ... | ... | ... | ... |

<!-- Tier 3 only -->
## Manual Migration Steps

- [ ] {Step requiring human judgment — for example, place secondary actors in levels}
- [ ] ...
~~~

Do NOT write `01-pre-migration.json` or `02-migration-plan.json`. All this data is now inline.

Optional `design.md` decision (make this decision NOW, during ANALYZE): Only create a separate `design.md` if ANY of:
- Multi-pass migration (`total_planned_passes > 1`)
- Any HIGH risk items (timelines, event dispatchers, interfaces)
- Deferred groups that need explanation
- Complex dependency chains requiring detailed analysis

Simple migrations (like BP_JumpPad: high confidence, 0 referencers, no timelines) should NOT generate `design.md`.

**If `--audit` flag:** Save the migration report to file (see below), then present design and exit.

### Save Migration Report to File

**After presenting the migration design (audit or full mode), always save the complete recommendations to a persistent file.** This ensures the analysis survives editor restarts and can be referenced in future sessions.

Write to: `docs/migration/blueprint-to-cpp/{BP_Name}/migration-report.md`

Contents:
- Audit summary (outcome, reasoning)
- Migration analysis table (what moves, what stays, why)
- Blueprint integration guide (what to remove, what to keep, step-by-step integration)
- Warnings and notes
- Timestamp

Report to user: "Migration report saved to `docs/migration/blueprint-to-cpp/{BP_Name}/migration-report.md`"

### Migration Complexity Classification

After ANALYZE completes, classify the migration as simple or complex:

Simple migration (ALL must be true):
- `migration_confidence` = high
- `referencers` = 0
- `blueprint_children_count` = 0
- No timelines
- No event dispatchers
- No interfaces implemented
- Parent is a C++ class (not another Blueprint)
- Single migration pass (`total_planned_passes` = 1)
- No UserConstructionScript nodes beyond visual sync (see cpp-migration.md "Visual Sync Classification")

Complex migration: anything that fails one or more simple criteria.

Record in frontmatter: `complexity: simple` or `complexity: complex`.

This classification determines the agent dispatch strategy in EXECUTE stage.

---

## Stage 2: PLAN

**Goal:** Generate complete C++ code and a granular task list. All hard thinking happens here — EXECUTE is mechanical.

### Step 1: Inspect Migrating Graph Nodes (Ground Truth)

Before generating any C++ code, inspect the actual Blueprint graph nodes to understand exactly what functions are called, what casts are performed, and what properties are accessed.

Scope limitation: `graph_list_nodes` and `graph_get_node` query `UbergraphPages` and `FunctionGraphs` only. They do NOT reach macro graphs, delegate signature graphs, or collapsed subgraphs. If the pre-migration snapshot shows macro instances or collapsed graphs, flag them as requiring manual review.

**Compact mode warning:** `graph_list_nodes` and `graph_get_node` default to `compact=true`, which strips positions, `node_class`, `pin_count`, and hidden pins with no connections or defaults. **Migration MUST pass `compact=false`** on every call in this section. The Ground Truth Table depends on full fidelity — missing hidden pins means missing world-context arguments in generated C++, and missing `position`/`pin_count` breaks downstream completeness checks.

For each graph listed as "migrating" in the approved design:

1. Call `graph_list_nodes` with the Blueprint path, graph name, and `compact=false`
   - This returns: node_id, class, node_class, display_name, position, pin_count for every node
2. For each node that is or inherits from `K2Node_CallFunction` (including `K2Node_CallParentFunction`, `K2Node_CallArrayFunction`):
   - Call `graph_get_node` with `compact=false` to get full pin details (including hidden class-reference and world-context pins)
   - Extract the target function name from `display_name`
   - IMPORTANT: The display name is human-readable (for example, "Launch Character"), not the C++ function name. The actual C++ function may have a `K2_` prefix (for example, `K2_SetActorLocation` not `SetActorLocation`). Cross-reference with UE documentation or `reflect.class_detail` to get the exact C++ function signature when in doubt.
   - Record: `{node_id, display_name, inferred_function_name, target_class, parameters}`. **Always use `display_name` for user-facing references** (e.g., "Launch Character", not "K2Node_CallFunction_19")
3. For each `K2Node_DynamicCast`:
   - Record the target class being cast to
4. For each `K2Node_VariableGet` or `K2Node_VariableSet`:
   - Record the variable name and whether it is a get or set
5. For each `K2Node_ComponentBoundEvent`:
   - Record the component name and event name (for example, OnComponentBeginOverlap)
   - These require `AddDynamic` delegate binding in C++ — do not confuse with direct function calls
6. For each `K2Node_CallDelegate` or `K2Node_AssignDelegate`:
   - Record the delegate name and binding pattern
7. For latent function calls (`K2Node_CallFunction` where the function is latent — look for "Latent" in display name or node class):
   - Flag as requiring special C++ treatment (FTimerHandle, async patterns, or UE5 subsystem async)

Build a "Ground Truth Table" and append to migration-plan.md after the Migration Scope section:

#### Unified Ground Truth Table Format

The Ground Truth Table uses a single format for all migrations. For standard (non-redesign) migrations, `Target Class` defaults to the single target class and `Automated` defaults to `Yes`.

**Node naming rule:** The `Display Name` column uses the human-readable name from `GetNodeTitle` (e.g., "Launch Character", "Set Actor Location"). The `Node ID` column stores the internal ID (e.g., "K2Node_CallFunction_19") for MCP tool calls only. When referencing nodes in user-facing output (chat, reports, tables), ALWAYS use `Display Name`, NEVER `Node ID`.

~~~markdown
## Ground Truth Table

| Node ID | Display Name | Type | Function/Property | Target | Parameters | Notes | Target Class | Automated |
|---------|-------------|------|-------------------|--------|------------|-------|-------------|-----------|
| K2Node_CallFunction_3 | Launch Character | CallFunction | LaunchCharacter | ACharacter | FVector, bool, bool | | AMyCharacterBase | Yes |
| K2Node_VariableGet_7 | Get Velocity | VariableGet | Velocity | Self | -- | | AMyCharacterBase | Yes |
| K2Node_DynamicCast_1 | Cast To ACharacter | Cast | ACharacter | OtherActor | -- | | AMyCharacterBase | Yes |
| K2Node_ComponentBoundEvent_0 | OnComponentBeginOverlap (CollisionComp) | ComponentBoundEvent | OnComponentBeginOverlap | CollisionComp | -- | Needs AddDynamic | UCollisionComponent | Yes |
| K2Node_CallDelegate_2 | Call OnJumpComplete | CallDelegate | OnJumpComplete | Self | -- | DECLARE_DYNAMIC_MULTICAST_DELEGATE | AMyCharacterBase | Yes |
~~~

For redesign migrations, `Target Class` is set per-row based on the responsibility map. For Tier 3, rows targeting secondary actor classes have `Automated: No`.

The executor acts on the `Automated` column: `Yes` = clean up automatically, `No` = leave with annotation.

Flag unmappable nodes as WARNING (use display name):
`WARNING: "ForEachLoop" (MacroInstance) has no direct C++ equivalent. Recommend: Replace with standard for-loop in C++ implementation.`

Feed this table into code generation. The generated C++ must use exactly the functions found in the graph — not assumed equivalents.

### Step 2: Generate C++ Code

Using the approved design, Ground Truth Table, and the `cpp-migration-specialist` agent patterns (see `resources/cpp-migration.md`):

1. Generate complete C++ header file
2. Generate complete C++ source file
3. Generate Build.cs patch (if module dependencies needed)

Code generation rules (from cpp-migration.md resource):
- Read all defaults from pre-migration snapshot — never hallucinate values
- Component names must match SCS variable names exactly (for hierarchy walking)
- Always include `Super::BeginPlay()`, `Super::Tick()`, `Super::OnConstruction()` where applicable
- Construction script → `OnConstruction()` override (NOT constructor), unless only visual-sync nodes
- Timelines → `UTimelineComponent` + curve setup in BeginPlay
- Event dispatchers → `DECLARE_DYNAMIC_MULTICAST_DELEGATE`
- Follow `docs/unreal-coding-standards.md` (Epic standard)

#### Multi-File Code Generation (When Goal = "Redesign/restructure")

For redesign migrations, PLAN generates multiple `.h`/`.cpp` file pairs:

1. **Primary class** — inherits from BP's parent class. Constructor includes `CreateDefaultSubobject<>()` calls for Tier 1 components, plus `SetupAttachment(RootComponent)` for any `USceneComponent` subclasses. Holds cached `UPROPERTY()` pointers to each component.
2. **Component classes** (Tier 1) — one `.h`/`.cpp` pair per extracted component. Use `USceneComponent` for spatial responsibilities, `UActorComponent` for pure logic.
3. **Utility classes** (Tier 2) — one `.h`/`.cpp` pair per subsystem or function library.
4. **Secondary actor classes** (Tier 3) — one `.h`/`.cpp` pair per split-off actor. Include TODO comments for manual wiring.

**All generated classes must go in the same module** (same Build.cs). Cross-module generation is not supported.

**Forward declarations:** Component headers forward-declare the owner; owner header forward-declares components. Full includes in `.cpp` files only. UHT needs full type only for `TSubclassOf<>` and `meta=` specifiers — use raw pointers in cross-class `UPROPERTY()` declarations.

**Include ordering in `.cpp`:** matching header first, then engine headers, then project headers.

Single UBT build for all files at once. If build fails, parse compiler error output to identify which generated file contains the error, present the error with file context, and offer to fix.

**Build.cs dependency analysis:** During PLAN (not deferred), identify any new module dependencies required by extracted classes and list them explicitly in the migration plan.

Update `target_classes` in frontmatter and `files_created` for each generated file pair.

**Dynamic task numbering:** Generate one write-task per file pair. For a 3-class redesign, tasks become: "Write PrimaryClass .h/.cpp", "Write HealthComponent .h/.cpp", "Write InventoryComponent .h/.cpp", then "Build all C++."

### Step 2.5: Cross-Reference Generated Code Against Graph Nodes

After generating C++ code but before writing it to the plan document:

1. For each row in the Ground Truth Table, search the generated `.cpp` for the function/property name
   - If the function name appears in a method call context -> PASS
   - If the function name appears but with different parameters -> WARNING: `Parameter mismatch for {function}`
   - If the function name is not found anywhere in generated code -> ERROR: `Missing C++ equivalent for BP node {node_id}: {function}`
   - If you generate a function call that does NOT appear as a node in the Ground Truth Table -> IMPROVEMENT: `Node {node_id} ({original_function}) replaced with {new_function}. Moved to Optional Improvement section.`
2. **Mechanical test for faithful vs. improvement:** Every `graph_get_node` result must map 1:1 to a line of generated C++. If you are generating a function call that does NOT appear as a node in the Ground Truth Table, it is an improvement, not a translation. Move it to a separate "Optional Improvement" section in the generated code.
3. If any ERRORs found:
   - Do NOT proceed to the hard gate
   - Present the mismatches to the user
   - Revise the generated code to match the actual graph nodes
   - Re-run the cross-reference check
4. If any IMPROVEMENTs found:
   - Generate TWO code sections: "Generated C++ — Faithful Translation" (exact node-by-node) and "Optional: Suggested Improvement" (with the improved version and explanation)
   - Both sections go into the plan document
   - The faithful version is the default — improvements only apply on explicit user approval at the plan review gate
5. If only WARNINGs (no ERRORs, no IMPROVEMENTs):
   - Include them in the plan document as a "Code Generation Notes" subsection under Generated C++ Code
   - Proceed to the hard gate (user can review)

Append generated C++ code inline to `migration-plan.md` under a new section. Use the Edit tool to insert after the `## Ground Truth Table` section (or after `## Migration Scope` if Ground Truth Table was not created):

~~~markdown
## Generated C++ Code

### Header ({ClassName}.h)

```cpp
// Full generated header content here
```

### Source ({ClassName}.cpp)

```cpp
// Full generated source content here
```

### Build.cs Changes (if needed)

```csharp
// Module dependency additions
```
~~~

For standard migrations, do NOT create a `generated/` directory or separate `.h`/`.cpp` files. The code lives in the plan document until Tasks 5-6 copy it to the actual source paths. For redesign migrations generating 4+ files, generated code may be written to `docs/migration/blueprint-to-cpp/{BP_Name}/generated/` and referenced from `files_created`.

Note for Tasks 5-6 (PREPARE phase): When writing C++ files to disk, extract the code from the fenced code blocks in `migration-plan.md`. Identify the correct block by its heading name (`### Header ({ClassName}.h)` or `### Source ({ClassName}.cpp)`), not by searching for arbitrary `cpp` blocks.

#### Context Management for Redesign

For redesign migrations generating 4+ files, generated C++ code may be written to `docs/migration/blueprint-to-cpp/{BP_Name}/generated/` instead of inline in migration-plan.md. Reference file paths in migration-plan.md via `files_created` frontmatter. The executor reads files from disk.

**Agent context scoping for redesign:** When dispatching the executor for cleanup tasks, include only:
- Frontmatter (full)
- Responsibility Map section
- Ground Truth Table (only rows relevant to current task range)
- Primary class code (for cleanup decisions)

Do NOT include all generated source files in the executor dispatch. The executor needs the responsibility map and ground truth to know what to clean, not the full source of every component class.

**Cross-reference check scaling:** For multi-class redesign, cross-reference the ground truth table per-class: for each target class, validate only the rows assigned to that class against that class's `.cpp` file. Do not search all `.cpp` files for every row.

### Step 3: Generate Task List

Generate a numbered task list following this template. Adapt task count based on the Blueprint's complexity (more components = more sub-tasks in Task 14, etc.):

```
── PREPARE ──────────────────────────────────────────────
Task 1: Verify MCP connection
Task 2: Verify Blueprint staleness
Task 3: Verify/update Build.cs dependencies
Task 4: Duplicate Blueprint
Task 5: Write C++ header
Task 6: Write C++ source
Task 7: Build project (outside editor)
Task 8: Restart editor (automated via cortex-editor), verify class registered

── EXECUTE (on BP_Name_Migration) ───────────────────────
Task 9: Validate component name collisions
Task 10: Reparent to C++ class
Task 11: Disconnect migrated event nodes (by GUID)
Task 12: Remove migrated functions (dependency order — one sub-task per function)
Task 13: Remove migrated variables (reverse-dependency order — one sub-task per variable)
Task 14: Remove migrated SCS components (one sub-task per component)

── MID-EXECUTION VERIFICATION ───────────────────────────
Task 15: Smoke test migrated copy

── VERIFY ───────────────────────────────────────────────
Task 16: Structural verification
Task 17: Dependency impact check

── SWAP ─────────────────────────────────────────────────
Task 18: Disable auto-save
Task 19: Execute rename swap
Task 19b: Remove orphaned nodes from migrated graphs
Task 19c: Save migrated Blueprint to disk
Task 20: Fix redirectors and recompile dependents
Task 21: Re-enable auto-save

── COMPLETE ─────────────────────────────────────────────
Task 22: Write final report
```

Each task must include:
- **Action** — exact MCP tools or file operations
- **Verify** — how to confirm success
- **Rollback** — what to undo on failure (file manifest for PREPARE, re-duplicate for EXECUTE, detailed steps for SWAP)

### Step 4: Update Plan Document

Append to the existing `migration-plan.md` (created in ANALYZE stage). Use the Edit tool to insert after the `## Generated C++ Code` section:

1. Update YAML frontmatter — set `total_tasks`, `status: planned`, `phase: plan`, populate `tasks` array, update `last_updated`
2. Append the task list section:

```markdown
## Task List

Each task includes Action, Verify, and Rollback:

### Task 1 -- Verify MCP connection
- **Action:** Invoke `/cortex-editor` to verify editor, MCP, and domain health
- **Verify:** Response includes expected domains
- **Rollback:** N/A

### Task 2 -- ...
(etc.)
```

### Step 5: Hard Gate — User Approves Plan

Present the plan summary:
- Total task count
- Phase breakdown
- C++ code preview (show key sections of generated header/source)
- Any HIGH risk items

**If IMPROVEMENTs were flagged in Step 2.5:** Before the main approval gate, present the faithful vs. improvement choice as a **required binary decision** using `AskUserQuestion`:

```
The cross-reference found suggested improvements to the faithful translation.

## Generated C++ — Faithful Translation
[code preview: exact translation of Blueprint logic]

## Optional: Suggested Improvement
[description of why the improvement is better]
[code preview: improved version]
```

Options:
- [Keep faithful translation] — use exact BP logic translation (default)
- [Apply improvement instead] — use the improved version

This choice is required — do not proceed without an explicit selection. If the user selects "Keep faithful translation", discard the improvement section from the plan document before proceeding.

**Then present the main approval gate** using `AskUserQuestion`:
- [Approve and execute] — proceed to EXECUTE stage
- [Review code] — show full generated C++ code for review
- [Adjust] — user requests changes to the plan
- [Cancel] — abort

On approval: update frontmatter `status: approved`.

---

## Stage 3: EXECUTE

**Goal:** Mechanically execute the approved plan with visual progress tracking.

### TaskCreate: Per-Phase

Do NOT create all tasks upfront. Create per-phase:

1. **Start:** Create PREPARE phase TaskCreate entries (Tasks 1-8) + one summary entry: "Upcoming: EXECUTE ({N} tasks) → VERIFY (2 tasks) → SWAP (5 tasks)"
2. **After PREPARE:** Create EXECUTE phase TaskCreate entries (Tasks 9-15)
3. **After EXECUTE:** Create VERIFY phase TaskCreate entries (Tasks 16-17)
4. **After VERIFY:** Create SWAP + COMPLETE TaskCreate entries (Tasks 18-22)

Mark each task `in_progress` when starting, `completed` when done.

### PREPARE Phase (Tasks 1-8) — Orchestrator Handles Directly

**NEVER dispatch a sub-agent for PREPARE tasks.** Call MCP tools and file operations directly in this conversation. If you reach for the Agent tool for any of Tasks 1-8, stop — that is incorrect. Tasks 1-8 are simple operations: status checks, file reads, build commands. They require no agent context and no agent overhead.

**CRITICAL: Frontmatter update after EVERY task, BEFORE proceeding to the next task.**

After completing each PREPARE task, immediately edit `migration-plan.md` frontmatter. Do not batch frontmatter updates — update after each individual task. Frontmatter is the durable store; TaskCreate is ephemeral session state. Update frontmatter BEFORE marking the TaskCreate entry as completed.

```yaml
# Update these fields after each task:
current_task: <N>           # The task just completed
last_updated: "<ISO-8601>"  # Current timestamp
tasks:
  - { id: <N>, status: completed }  # Mark the specific task
# Also update these when applicable:
files_created: [...]        # Append paths of new files (Tasks 5, 6)
files_modified: [...]       # Append paths of modified files (Task 3)
editor_restarts: <count>    # Increment after Task 8 restart
```

This is mandatory, not optional. The migration-plan.md is the single source of truth. If the session is interrupted during PREPARE and resumed later, `--resume` relies on these fields to know where to continue.

**Task sequence:**

| Task | Action | Frontmatter Update |
|------|--------|--------------------|
| 1 | Verify MCP connection via `/cortex-editor` | `current_task: 1`, task 1 completed |
| 2 | Staleness check: compare `blueprint_hash` | `current_task: 2`, task 2 completed |
| 3 | Check Build.cs for required modules | `current_task: 3`, task 3 completed, `files_modified` += Build.cs path (if changed) |
| 4 | Call `duplicate_blueprint` | `current_task: 4`, task 4 completed |
| 5 | Write C++ header to target path | `current_task: 5`, task 5 completed, `files_created` += header path |
| 6 | Write C++ source to target path | `current_task: 6`, task 6 completed, `files_created` += source path |
| 7 | Run UBT build, verify 0 errors/warnings | `current_task: 7`, task 7 completed |
| 8 | Invoke Skill tool: `skill: "cortex-editor"` — use its restart path and verify the target C++ class is registered in editor | `current_task: 8`, task 8 completed, **`phase: execute`**, `editor_restarts` += 1 |

**Task 8 is the PREPARE-to-EXECUTE transition.** It is the only task that changes the `phase` field. Update `phase: execute` in addition to `current_task: 8`.

**Example frontmatter edit after Task 5:**

```yaml
current_task: 5
last_updated: "2026-02-27T14:30:00.000Z"
files_created:
  - "Source/CortexSandbox/Public/JumpPad/AJumpPad.h"
tasks:
  - { id: 1, status: completed }
  - { id: 2, status: completed }
  - { id: 3, status: completed }
  - { id: 4, status: completed }
  - { id: 5, status: completed }
  - { id: 6, status: pending }
  # ... rest unchanged
```

**On failure:** Set `status: failed`, `failed_task: <N>` BEFORE presenting recovery options. This ensures the failure point is persisted even if the session crashes.

### Agent Dispatch Strategy

Simple migrations -- 2 dispatches:

| Phase | Handler | Rationale |
|-------|---------|-----------|
| PREPARE (Tasks 1-8) | Orchestrator inline | No agent needed for file ops + build |
| EXECUTE (Tasks 9-15) | Executor agent (sonnet) | Multi-step MCP workflow, needs dedicated agent |
| VERIFY (Tasks 16-17) | Orchestrator inline | Simple: compile check + component delta + orphan check. No full verifier needed. |
| SWAP + COMPLETE (Tasks 18-22) | Finalizer agent (sonnet) | Rename swap is critical, needs dedicated agent |

Complex migrations -- 3 dispatches (unchanged):

| Phase | Handler | Rationale |
|-------|---------|-----------|
| PREPARE (Tasks 1-8) | Orchestrator inline | Same as simple |
| EXECUTE (Tasks 9-15) | Executor agent (sonnet) | Same as simple |
| VERIFY (Tasks 16-17) | Verifier agent (sonnet) | Full structural comparison, dependency impact analysis needed |
| SWAP + COMPLETE (Tasks 18-22) | Finalizer agent (sonnet) | Same as simple |

### Inline Verification (Simple Migrations Only)

When `complexity: simple`, the orchestrator handles VERIFY directly instead of dispatching the verifier agent:

Task 16 -- Simplified Structural Verification:
1. Call `blueprint_cmd(command="compile", params={"asset_path": "/Game/.../BP_Name_Migration"})` -> must compile clean
2. Call `analyze_blueprint_for_migration` on `BP_Name_Migration`:
   - Verify parent class is the target C++ class
   - Check that migrated variables are gone
   - Check that migrated functions are gone
   - Component count delta: post-migration SCS component count should equal `pre_migration_scs_count - migrated_component_count`. The migrated components now live in the C++ class (via `CreateDefaultSubobject`), so they should have been removed from the Blueprint's SCS.
3. Check for orphaned nodes: if any migrated graphs had events disconnected, verify node count decreased (orphans were deleted by executor step 3b)

Task 17 -- Simplified Dependency Check:
- Skip entirely if `referencers = 0` (already known from ANALYZE)
- If referencers > 0 (should not happen for simple migrations): fall back to full verifier agent

Verification gate:

```text
Verification (inline -- simple migration):
  Compile: clean
  Parent: {ClassName} [PASS]
  Components: {post_count}/{expected_count} [PASS]
  Migrated vars removed: [PASS]
  Migrated funcs removed: [PASS]
  Orphaned nodes: 0

Note: CDO property comparison was skipped (simple migration).
Verify runtime behavior after swap.

[Swap] -- proceed to rename swap
[Fix]  -- address issues first
[Stop] -- save progress
```

Fallback: If any inline check fails unexpectedly, dispatch the full verifier agent instead of trying to diagnose inline. Report: "Inline verification found issues -- dispatching full verifier for detailed analysis."

### EXECUTE Phase (Tasks 9-15) — Dispatch Executor Agent

**Pre-dispatch:** Run Pre-Dispatch Protocol (see above).

Dispatch `cortex-toolkit:bp-migration-executor` with:
- Relevant sections of migration-plan.md (see Agent Context Scoping in Implementation Notes)
- Task range: 9-15

The executor appends execution results to `migration-plan.md` and returns concise status.

**Tier 3 pause (When `goal: redesign` and `redesign_tier: 3`):** After executor completes, present the `## Manual Migration Steps` checklist from migration-plan.md to the user. Pause and wait for user confirmation that manual steps are done before proceeding to VERIFY. Ask via `AskUserQuestion`:
```
The automated portion of the Tier 3 migration is complete.
These manual steps remain before verification:
{list from Manual Migration Steps}

[Done — proceed to verify]
[Need help with a step]
[Pause — resume later]
```

### Crash Recovery (Orchestrator)

When a phase agent returns `status: editor_crashed`:

1. Use the Skill tool: `skill: "cortex-editor"` to diagnose the state
2. If editor is dead (status shows "Editor not running" or stale port):
   a. Use the Skill tool: `skill: "cortex-editor"` and use its restart path (editor crashed, nothing to save)
      - The skill handles stale port file cleanup, process verification, and MCP reconnection
   b. Verify `reflect` and `blueprint` domains are registered in the restart response
   c. Verify class registration via `reflect.class_detail` (if post-build)
   d. Increment `editor_restarts` in frontmatter. If >= 3, hard stop (see Pipeline-Wide Restart Limit)
3. **Re-verify asset state before resuming** (critical for mid-EXECUTE/SWAP crashes):
   - If crash during EXECUTE: verify the duplicate Blueprint exists and is not corrupted (`get_blueprint_details`)
   - If crash during VERIFY: VERIFY is read-only — safe to retry from `failed_task` without re-verification of asset state
   - If crash during SWAP: verify which referencers have already been updated (`get_referencers`). Do NOT blindly re-run from `failed_task` — some referencers may already point to the new asset
   - The frontmatter `failed_task` indicates where to resume, but the orchestrator must confirm preconditions of that task still hold
4. Resume from `failed_task` by re-dispatching the phase agent with updated task range
5. Update frontmatter: refresh `last_updated`, keep `status: executing`
6. If restart fails after 2 attempts, present via AskUserQuestion:
   ```
   Editor crashed and could not be restarted. Options:
   [1] Retry restart
   [2] Manual — I'll restart the editor myself, tell me when ready
   [3] Stop — save progress, resume later with --resume
   ```
   If user picks [2] Manual: wait for user confirmation, then run `/cortex-editor` to verify before proceeding.

### VERIFY Phase (Tasks 16-17)

**Pre-dispatch:** Run Pre-Dispatch Protocol (see above).

If `complexity: simple`:
Run Inline Verification (see above). No agent dispatch.

If `complexity: complex`:
Dispatch `cortex-toolkit:bp-migration-verifier` with:
- Relevant sections of migration-plan.md (see Agent Context Scoping in Implementation Notes)
- Task range: 16-17

The verifier appends results to `migration-plan.md` and returns a concise summary.

### Hard Gate — User Reviews Verification

Present verification summary. Ask for approval:
- [Swap] — proceed to rename swap
- [Fix] — address issues first (loop back to executor)
- [Pause] — save state, resume later
- [Abort] — delete migration copy, keep original. Clean up: delete `BP_Name_Migration`, delete C++ files, update frontmatter `status: failed`.

### SWAP + COMPLETE Phase (Tasks 18-22) — Dispatch Finalizer Agent

**Pre-dispatch:** Run Pre-Dispatch Protocol (see above).

Dispatch `cortex-toolkit:bp-migration-finalizer` with:
- Relevant sections of migration-plan.md (see Agent Context Scoping in Implementation Notes)
- Task range: 18-22

The finalizer returns:
- Swap status (success or failure with details)
- `rollback.json` written to disk and Final Report appended to `migration-plan.md`

### Failure Handling

On any task failure from any agent:

1. Update frontmatter: `status: failed`, `failed_task: {N}`
2. Present to user:
   ```
   Task {N} failed: {task title}
   Error: {error message}

   [fix]  — Investigate and fix the issue, then retry
   [skip] — Skip this task and continue (only if independent)
   [stop] — Save progress, resume later with --resume
   ```
3. On **[fix]**: analyze error, propose fix, apply to file AND update plan document, retry task
4. On **[skip]**: mark task as skipped in frontmatter, continue
5. On **[stop]**: save frontmatter, exit

---

## Stage 4: COMPLETE (Post-Swap)

After the finalizer succeeds:

### Step 1: Present Migration Results

Display a summary (not a menu -- just information):

```text
Migration Complete: {BP_Name} -> {ClassName}

  C++ class: {ClassName} ({header_path})
  Blueprint: /Game/.../{BP_Name} (reparented to {ClassName})
  Plan: docs/migration/blueprint-to-cpp/{BP_Name}/migration-plan.md
```

### Step 2: Handle Backup

Read `backup_verified` from the finalizer response (or from `rollback.json`).

If `backup_verified: false`:
- Report: `No backup preserved -- the original Blueprint was replaced directly via redirector chain. This is normal when rename redirectors are resolved.`
- Skip the backup menu entirely.

If `backup_verified: true`:
- Use `AskUserQuestion`:

```text
What would you like to do with the backup?
[1] Keep -- BP_Name_Backup stays in place as a safety net
[2] Archive -- move to /Game/Migration/Backups/BP_Name_Backup
[3] Delete -- remove the backup (migration confirmed clean)
```

- On [1] Keep: no action needed
- On [2] Archive: call `rename_blueprint` to move to `/Game/Migration/Backups/`, then call `fixup_redirectors` on the source directory to resolve the redirector left behind
- On [3] Delete: call `delete_blueprint`. If delete fails (asset not found), report warning but do not treat as error — the asset may have been consumed by redirector resolution.

### Step 3: Update Plan Document

The finalizer already appended the Final Report section. Update frontmatter: `status: completed`, `phase: complete`.

### Step 4: Show Deferred Groups (Multi-Pass Only)

For partial migrations (`total_planned_passes > 1`), show:
- Which groups were migrated this pass
- Which groups are deferred to future passes
- Note: next pass requires editor restart (class layout changes)

### Step 5: Note for User (Simple Migrations)

If `complexity: simple`, add:

```text
Note: CDO (Class Default Object) property comparison was skipped for
this simple migration. Verify runtime behavior matches expectations
(component properties, default values, collision settings).
```

---

## Supported Blueprint Types

- **Actor Blueprints** — migrated to C++ base class (AActor or existing C++ parent subclass)
- **Widget Blueprints** — migrated to C++ UUserWidget subclass with BindWidget
- **Component Blueprints** — migrated to C++ UActorComponent/USceneComponent subclass
- **FunctionLibrary Blueprints** — migrated to C++ UBlueprintFunctionLibrary with static functions
- **Interface Blueprints** — migrated to C++ UInterface + IInterface pair

## References

- Design: `docs/plans/2026-02-27-bp-migration-pipeline-design.md`
- V5 schema: `docs/plans/2026-02-26-bp-migration-v5-design.md`
- Patterns: `resources/cpp-migration.md`
- Standards: `docs/unreal-coding-standards.md`
