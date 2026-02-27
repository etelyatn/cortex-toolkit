---
name: cortex-bp-migrate
description: Blueprint-to-C++ migration pipeline with conversational analysis, plan-driven execution, visual progress tracking, and hard gates. Supports --audit and --resume.
---

# Blueprint to C++ Migration Pipeline

Migrate a Blueprint to C++ using a 4-stage pipeline: ANALYZE → PLAN → EXECUTE → COMPLETE. Each stage has a hard gate requiring user approval before proceeding.

## Entry Point

Parse user input for:
- **Blueprint path** (required) — e.g., `BP_JumpPad` or `/Game/Blueprints/BP_JumpPad`
- **`--audit`** — run ANALYZE stage only, present design without executing
- **`--resume`** — detect and resume from saved migration state

## Resume Detection

If `--resume` flag OR `docs/migration/blueprint-to-cpp/{BP_Name}/migration-plan.md` exists:

1. Read `migration-plan.md` YAML frontmatter
2. Parse: `status`, `current_task`, `failed_task`, `phase`, `blueprint_hash`
3. Verify workspace state:
   - Do files in `files_created` actually exist on disk?
   - Does `BP_Name_Migration` copy exist in the editor?
   - Does the C++ class exist and compile?
   - Does `blueprint_hash` match current Blueprint? (staleness check)
4. Present resume point to user with options: [resume / rewind / restart]
5. On resume: create TaskCreate entries for remaining tasks, continue from saved phase

## Pre-Flight Check (Task 0)

Before entering any stage, verify the editor is alive and MCP is healthy.

**Steps:**
1. Use the Skill tool: `skill: "cortex-status"` — checks the full diagnostic chain (editor process, port file, MCP connection, domains)
   - If all checks pass AND `blueprint` domain is registered -> proceed to ANALYZE
   - If editor not running OR port file stale -> go to step 2
   - If MCP connection fails but editor is running -> go to step 3
   - If `blueprint` domain is missing -> editor may need full restart (not just reconnect). Run `/cortex-restart`, then re-run `/cortex-status`

2. **Editor not running:** Use the Skill tool: `skill: "cortex-editor"` to start the editor
   - The skill handles: engine path lookup, background launch with `-AutoDeclinePackageRecovery`, port file polling (120s timeout), MCP verification
   - After skill completes -> re-run `/cortex-status` to confirm `blueprint` domain is registered

3. **MCP connection failed (editor running):** Use the Skill tool: `skill: "cortex-reconnect"`
   - `/cortex-reconnect` retries `get_status` up to 4 times over ~55 seconds. It is for when the editor process is healthy but the MCP client lost its connection. Prefer this over a full restart when the editor is still running.
   - If reconnect fails -> use `/cortex-restart` (full restart cycle)

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
If user picks [2] Manual: wait for user to confirm editor is ready, then run `/cortex-status` to verify MCP connection and `blueprint` domain before proceeding.

**Note:** Do NOT use inline bash commands (`tasklist`, `grep`, port file globbing) for editor lifecycle operations. Always delegate to the Cortex core skills which handle edge cases (stale port files, PID validation, multiple editor instances) consistently.

### Pipeline-Wide Restart Limit

Track editor restarts in frontmatter field `editor_restarts`.

- Hard cap: `3` total restarts across the full migration pipeline
- Increment after every successful orchestrator-triggered restart (`/cortex-restart`)
- If `editor_restarts >= 3`: stop immediately and present:
  ```
  Editor has restarted 3 times in this migration.
  This usually indicates an underlying engine/plugin issue.
  Please investigate manually (logs, crash report, plugin state), then resume with --resume.
  ```

### Pre-Dispatch Protocol (referenced by all phase dispatches)

Before dispatching ANY phase agent (executor, verifier, finalizer):
1. Run `/cortex-status` — verify editor alive + MCP connected + `blueprint` domain registered
2. If editor is down -> use `/cortex-editor` or `/cortex-restart` as appropriate
3. Only dispatch agent once MCP connection is confirmed and `blueprint` domain is registered
4. If editor cannot be started after 2 attempts (respecting pipeline-wide restart cap) -> present:
   ```
   Editor is down before agent dispatch. Options:
   [1] Retry — try starting editor again
   [2] Manual — I'll start it myself, then continue
   [3] Stop — save progress, resume later with --resume
   ```
   If user picks [2] Manual: wait for confirmation, re-run `/cortex-status` before dispatching.

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
| Finalizer | Frontmatter + Execution Log + Verification Results + Task List (tasks in range only) |

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

## Stage 1: ANALYZE

**Goal:** Understand user goals, analyze the Blueprint technically, present a migration design for approval.

### Step 1: Ask Goal Questions (Conversational — Before Any MCP Calls)

Use `AskUserQuestion` to ask one question at a time:

1. "Why are you migrating this Blueprint?" — options: Performance, Reusability/base class, Complexity management, Cleanup/tech debt
2. "Any constraints for this migration?" — options: Keep specific things in BP, Avoid adding module dependencies, No constraints
3. "What scope are you thinking?" — options: Everything possible, Logic only (keep visual BP), Specific features (I'll choose), Not sure (recommend for me)

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

### Step 3: Present Migration Design

Synthesize user goals (Step 1) with technical analysis (Step 2). Present:

1. **Blueprint summary** — components, variables, functions, complexity, parent class
2. **Functional groups** with coupling warnings (max 6 groups; merge small ones)
3. **Dependency impact table** — SAFE/WARNING/BREAKING per public member
4. **Scope recommendation** — based on user's stated goals
5. **MIGRATING / STAYING / DEFERRED columns** — what moves to C++, what stays in BP, what's deferred

### Step 4: Hard Gate — User Approves Design

Present the migration design and ask for approval using `AskUserQuestion`:
- [Approve] — proceed to PLAN stage
- [Adjust] — user modifies scope, moves items between columns
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
~~~

Do NOT write `01-pre-migration.json` or `02-migration-plan.json`. All this data is now inline.

Optional `design.md` decision (make this decision NOW, during ANALYZE): Only create a separate `design.md` if ANY of:
- Multi-pass migration (`total_planned_passes > 1`)
- Any HIGH risk items (timelines, event dispatchers, interfaces)
- Deferred groups that need explanation
- Complex dependency chains requiring detailed analysis

Simple migrations (like BP_JumpPad: high confidence, 0 referencers, no timelines) should NOT generate `design.md`.

**If `--audit` flag:** Stop here. Present design and exit.

---

## Stage 2: PLAN

**Goal:** Generate complete C++ code and a granular task list. All hard thinking happens here — EXECUTE is mechanical.

### Step 1: Inspect Migrating Graph Nodes (Ground Truth)

Before generating any C++ code, inspect the actual Blueprint graph nodes to understand exactly what functions are called, what casts are performed, and what properties are accessed.

Scope limitation: `graph_list_nodes` and `graph_get_node` query `UbergraphPages` and `FunctionGraphs` only. They do NOT reach macro graphs, delegate signature graphs, or collapsed subgraphs. If the pre-migration snapshot shows macro instances or collapsed graphs, flag them as requiring manual review.

For each graph listed as "migrating" in the approved design:

1. Call `graph_list_nodes` with the Blueprint path and graph name
   - This returns: node_id, class, display_name, position, pin_count for every node
2. For each node that is or inherits from `K2Node_CallFunction` (including `K2Node_CallParentFunction`, `K2Node_CallArrayFunction`):
   - Call `graph_get_node` to get full pin details
   - Extract the target function name from `display_name`
   - IMPORTANT: The display name is human-readable (for example, "Launch Character"), not the C++ function name. The actual C++ function may have a `K2_` prefix (for example, `K2_SetActorLocation` not `SetActorLocation`). Cross-reference with UE documentation or `reflect.class_detail` to get the exact C++ function signature when in doubt.
   - Record: `{node_id, display_name, inferred_function_name, target_class, parameters}`
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

~~~markdown
## Ground Truth Table

| Node ID | Type | Function/Property | Target | Parameters | Notes |
|---------|------|-------------------|--------|------------|-------|
| N_123 | CallFunction | LaunchCharacter | ACharacter | FVector, bool, bool | |
| N_456 | VariableGet | Velocity | Self | -- | |
| N_789 | Cast | ACharacter | OtherActor | -- | |
| N_012 | ComponentBoundEvent | OnComponentBeginOverlap | CollisionComp | -- | Needs AddDynamic |
| N_345 | CallDelegate | OnJumpComplete | Self | -- | DECLARE_DYNAMIC_MULTICAST_DELEGATE |
~~~

Flag unmappable nodes as WARNING:
`WARNING: Node N_999 (UK2Node_MacroInstance: "ForEachLoop") has no direct C++ equivalent. Recommend: Replace with standard for-loop in C++ implementation.`

Feed this table into code generation. The generated C++ must use exactly the functions found in the graph — not assumed equivalents.

### Step 2: Generate C++ Code

Using the approved design, Ground Truth Table, and the `cpp-migration-specialist` agent patterns (see `cortex-blueprint/resources/cpp-migration.md`):

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

### Step 2.5: Cross-Reference Generated Code Against Graph Nodes

After generating C++ code but before writing it to the plan document:

1. For each row in the Ground Truth Table, search the generated `.cpp` for the function/property name
   - If the function name appears in a method call context -> PASS
   - If the function name appears but with different parameters -> WARNING: `Parameter mismatch for {function}`
   - If the function name is not found anywhere in generated code -> ERROR: `Missing C++ equivalent for BP node {node_id}: {function}`
2. If any ERRORs found:
   - Do NOT proceed to the hard gate
   - Present the mismatches to the user
   - Revise the generated code to match the actual graph nodes
   - Re-run the cross-reference check
3. If only WARNINGs:
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

Do NOT create a `generated/` directory or separate `.h`/`.cpp` files. The code lives in the plan document until Tasks 5-6 copy it to the actual source paths.

Note for Tasks 5-6 (PREPARE phase): When writing C++ files to disk, extract the code from the fenced code blocks in `migration-plan.md`. Identify the correct block by its heading name (`### Header ({ClassName}.h)` or `### Source ({ClassName}.cpp)`), not by searching for arbitrary `cpp` blocks.

### Step 2: Generate Task List

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
Task 8: Restart editor (automated via cortex-restart), verify class registered

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
Task 20: Fix redirectors and recompile dependents
Task 21: Re-enable auto-save

── COMPLETE ─────────────────────────────────────────────
Task 22: Write final report
```

Each task must include:
- **Action** — exact MCP tools or file operations
- **Verify** — how to confirm success
- **Rollback** — what to undo on failure (file manifest for PREPARE, re-duplicate for EXECUTE, detailed steps for SWAP)

### Step 3: Update Plan Document

Append to the existing `migration-plan.md` (created in ANALYZE stage). Use the Edit tool to insert after the `## Generated C++ Code` section:

1. Update YAML frontmatter — set `total_tasks`, `status: planned`, `phase: plan`, populate `tasks` array, update `last_updated`
2. Append the task list section:

```markdown
## Task List

Each task includes Action, Verify, and Rollback:

### Task 1 -- Verify MCP connection
- **Action:** Call `get_status` via `/cortex-status`
- **Verify:** Response includes expected domains
- **Rollback:** N/A

### Task 2 -- ...
(etc.)
```

### Step 4: Hard Gate — User Approves Plan

Present the plan summary:
- Total task count
- Phase breakdown
- C++ code preview (show key sections of generated header/source)
- Any HIGH risk items

Ask for approval using `AskUserQuestion`:
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

These are simple operations the orchestrator runs directly (no agent dispatch).

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
| 1 | Verify MCP connection via `/cortex-status` | `current_task: 1`, task 1 completed |
| 2 | Staleness check: compare `blueprint_hash` | `current_task: 2`, task 2 completed |
| 3 | Check Build.cs for required modules | `current_task: 3`, task 3 completed, `files_modified` += Build.cs path (if changed) |
| 4 | Call `duplicate_blueprint` | `current_task: 4`, task 4 completed |
| 5 | Write C++ header to target path | `current_task: 5`, task 5 completed, `files_created` += header path |
| 6 | Write C++ source to target path | `current_task: 6`, task 6 completed, `files_created` += source path |
| 7 | Run UBT build, verify 0 errors/warnings | `current_task: 7`, task 7 completed |
| 8 | Restart editor via `/cortex-restart`, verify class | `current_task: 8`, task 8 completed, **`phase: execute`**, `editor_restarts` += 1 |

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

### EXECUTE Phase (Tasks 9-15) — Dispatch Executor Agent

**Pre-dispatch:** Run Pre-Dispatch Protocol (see above).

Dispatch `cortex-blueprint:bp-migration-executor` with:
- Relevant sections of migration-plan.md (see Agent Context Scoping in Implementation Notes)
- Task range: 9-15

The executor appends execution results to `migration-plan.md` and returns concise status.

### Crash Recovery (Orchestrator)

When a phase agent returns `status: editor_crashed`:

1. Use the Skill tool: `skill: "cortex-status"` to diagnose the state
2. If editor is dead (status shows "Editor not running" or stale port):
   a. Use the Skill tool: `skill: "cortex-restart", args: "save=no build=no"` (editor crashed, nothing to save)
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
   If user picks [2] Manual: wait for user confirmation, then run `/cortex-status` to verify before proceeding.

### VERIFY Phase (Tasks 16-17) — Dispatch Verifier Agent

**Pre-dispatch:** Run Pre-Dispatch Protocol (see above).

Dispatch `cortex-blueprint:bp-migration-verifier` with:
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

Dispatch `cortex-blueprint:bp-migration-finalizer` with:
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
- On [3] Delete: call Blueprint `delete` tool. If delete fails (asset not found), report warning but do not treat as error — the asset may have been consumed by redirector resolution.

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
- Patterns: `cortex-toolkit/cortex-blueprint/resources/cpp-migration.md`
- Standards: `docs/unreal-coding-standards.md`
