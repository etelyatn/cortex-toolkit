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
   - If `blueprint` domain is missing -> editor may need full restart (not just reconnect). Go to step 2 with `/cortex-restart`

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

On approval:
- Write `docs/migration/blueprint-to-cpp/{BP_Name}/01-pre-migration.json` (V5 schema)
- Write `docs/migration/blueprint-to-cpp/{BP_Name}/02-migration-plan.json` (V5 schema)

**If `--audit` flag:** Stop here. Present design and exit.

---

## Stage 2: PLAN

**Goal:** Generate complete C++ code and a granular task list. All hard thinking happens here — EXECUTE is mechanical.

### Step 1: Generate C++ Code

Using the approved design and the `cpp-migration-specialist` agent patterns (see `cortex-blueprint/resources/cpp-migration.md`):

1. Generate complete C++ header file
2. Generate complete C++ source file
3. Generate Build.cs patch (if module dependencies needed)

Write generated code to:
- `docs/migration/blueprint-to-cpp/{BP_Name}/generated/{ClassName}.h`
- `docs/migration/blueprint-to-cpp/{BP_Name}/generated/{ClassName}.cpp`
- `docs/migration/blueprint-to-cpp/{BP_Name}/generated/Build.cs.patch` (if needed)

Code generation rules (from cpp-migration.md resource):
- Read all defaults from pre-migration snapshot — never hallucinate values
- Component names must match SCS variable names exactly (for hierarchy walking)
- Always include `Super::BeginPlay()`, `Super::Tick()`, `Super::OnConstruction()` where applicable
- Construction script → `OnConstruction()` override (NOT constructor), unless only visual-sync nodes
- Timelines → `UTimelineComponent` + curve setup in BeginPlay
- Event dispatchers → `DECLARE_DYNAMIC_MULTICAST_DELEGATE`
- Follow `docs/unreal-coding-standards.md` (Epic standard)

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

### Step 3: Write Plan Document

Write `docs/migration/blueprint-to-cpp/{BP_Name}/migration-plan.md` with:

1. **YAML frontmatter** — machine-readable state:
   ```yaml
   ---
   blueprint: /Game/Blueprints/{BP_Name}
   target_class: {ClassName}
   status: planned
   current_task: 0
   total_tasks: {N}
   failed_task: null
   phase: prepare
   created: {ISO timestamp}
   last_updated: {ISO timestamp}
   blueprint_hash: {hash from 01-pre-migration.json}
   migration_pass: 1
   total_planned_passes: {1 or more}
   deferred_groups: []
   tasks:
     - { id: 1, status: pending }
     # ... all tasks
   files_created: []
   files_modified: []
   ---
   ```

2. **Design Decisions section** — key reasoning from ANALYZE stage (3-5 bullets)

3. **Task list** — complete numbered tasks with actions, verification, and rollback

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

These are simple operations the orchestrator runs directly (no agent dispatch):

- **Tasks 1-2:** MCP connection check and staleness check
- **Task 3:** Check generated code imports against Build.cs, add missing modules
- **Task 4:** Call `duplicate_blueprint`
- **Tasks 5-6:** Write generated code from `generated/` directory to target paths
- **Task 7:** Run UBT build command, verify 0 errors/0 warnings
- **Task 8: Restart editor and verify class registration**
  1. Use the Skill tool: `skill: "cortex-restart", args: "save=yes build=no"` (Task 7 already built)
     - This handles: graceful shutdown -> wait for exit -> relaunch -> wait for port file -> verify MCP
  2. After restart completes, verify the `reflect` domain is listed in the restart response's `domains` field
     - If `reflect` domain missing: report error — CortexReflect plugin may not be enabled
  3. Verify the new C++ class is registered:
     - Call `reflect.class_detail` with the target class name (e.g., `AJumpPad`)
     - If class not found: the build may not have been loaded. Report error, present recovery menu
  4. Only fall back to asking the user if `/cortex-restart` fails after 2 attempts (and pipeline-wide restart cap not exceeded):
     ```
     Automated restart failed. Options:
     [1] Retry — try restarting again
     [2] Manual — I'll restart the editor myself, tell me when ready
     [3] Stop — save progress, resume later with --resume
     ```
  5. If user picks [2] Manual: wait for user to confirm editor is ready, then run `/cortex-status` to verify MCP connection before proceeding
  6. Update frontmatter: `current_task: 8`, `status: executing`, increment `editor_restarts`

Update frontmatter after each task: increment `current_task`, add to `files_created`/`files_modified`.

### EXECUTE Phase (Tasks 9-15) — Dispatch Executor Agent

**Pre-dispatch:** Run Pre-Dispatch Protocol (see above).

Dispatch `cortex-blueprint:bp-migration-executor` with:
- Full text of migration-plan.md
- Task range: 9-15
- Generated code directory path

The executor returns:
- Per-task status (completed or failed with error)
- 03-node-mapping.json written to disk

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
- Full text of migration-plan.md
- 01-pre-migration.json content
- Task range: 16-17

The verifier returns:
- Concise summary (components match, properties match, logic coverage, impact)
- 04-verification.json written to disk

### Hard Gate — User Reviews Verification

Present verification summary. Ask for approval:
- [Swap] — proceed to rename swap
- [Fix] — address issues first (loop back to executor)
- [Pause] — save state, resume later
- [Abort] — delete migration copy, keep original. Clean up: delete `BP_Name_Migration`, delete C++ files, update frontmatter `status: failed`.

### SWAP + COMPLETE Phase (Tasks 18-22) — Dispatch Finalizer Agent

**Pre-dispatch:** Run Pre-Dispatch Protocol (see above).

Dispatch `cortex-blueprint:bp-migration-finalizer` with:
- Full text of migration-plan.md
- All section file contents (01 through 04)
- Task range: 18-22

The finalizer returns:
- Swap status (success or failure with details)
- 05-rollback.json and report.json written to disk

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

After the finalizer succeeds, present results to user:

```
Migration Complete: {BP_Name} → {ClassName}

  Backup: /Game/Blueprints/{BP_Name}_Backup
  C++ class: {ClassName} ({header_path})
  Report: docs/migration/blueprint-to-cpp/{BP_Name}/report.json

  Backup handling:
  [keep]    — {BP_Name}_Backup stays in place
  [archive] — Move to /Game/Migration/Backups/
  [delete]  — Remove backup (not recommended)

  Optional cleanup:
  [clean]   — Remove orphaned nodes from event graph
  [skip]    — Leave orphaned nodes (safe, they don't execute)
```

Update frontmatter: `status: completed`.

For partial migrations, also show:
- Which groups were migrated this pass
- Which groups are deferred to future passes
- Note: next pass requires editor restart (class layout changes)

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
