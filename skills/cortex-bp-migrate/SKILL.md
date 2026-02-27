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
1. Glob for `Saved/CortexPort-*.txt`
   - If no port file found: invoke `cortex-editor` skill to start editor and wait for ready
   - If a port file exists: validate PID is alive with `tasklist /FI "PID eq {pid}" /NH`
     - If PID is not found: delete stale port file, then invoke `cortex-editor`
2. Call `get_status` MCP tool to verify the full chain
   - If it fails: invoke `cortex-editor` skill
3. Proceed only when `get_status` returns success

**Run this check:**
- At pipeline start (before ANALYZE)
- Before each phase agent dispatch (before EXECUTE, VERIFY, SWAP)
- After any editor crash recovery

**On failure after 2 retries:** present:
```
Editor could not be started. Options:
[1] Retry — try starting editor again
[2] Manual — I'll start it myself, then continue
[3] Stop — abort migration
```

### Editor Health Check (Reusable)

```bash
# 1. Find port file
PORT_FILE=$(ls Saved/CortexPort-*.txt 2>/dev/null | head -1)
if [ -z "$PORT_FILE" ]; then
  echo "NO_PORT_FILE"
  exit 0
fi

# 2. Extract PID from filename
PID=$(echo "$PORT_FILE" | grep -oP 'CortexPort-\K\d+')

# 3. Check if PID is alive
if ! tasklist /FI "PID eq $PID" /NH 2>/dev/null | grep -q "$PID"; then
  echo "STALE_PORT_FILE"
  rm "$PORT_FILE"
  exit 0
fi

# 4. Read port number
PORT=$(cat "$PORT_FILE")
echo "ALIVE:$PORT"
```

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
Task 8: Restart editor, verify class registered

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
- **Task 8:** Ask user to restart editor. Wait for confirmation. Verify MCP reconnects. Verify class exists via `query_class_hierarchy`.

Update frontmatter after each task: increment `current_task`, add to `files_created`/`files_modified`.

### EXECUTE Phase (Tasks 9-15) — Dispatch Executor Agent

Dispatch `cortex-blueprint:bp-migration-executor` with:
- Full text of migration-plan.md
- Task range: 9-15
- Generated code directory path

The executor returns:
- Per-task status (completed or failed with error)
- 03-node-mapping.json written to disk

### Crash Recovery (Orchestrator)

When a phase agent returns `status: editor_crashed`:

1. Run the Editor Health Check (from Task 0)
2. If editor is dead:
   a. Delete stale port file
   b. Invoke `cortex-restart` skill (`build=no`, `save=no`)
   c. Wait for MCP connection
   d. Verify class registration via `reflect.class_detail` (if post-build)
3. Resume from `failed_task` by re-dispatching the phase agent with updated task range
4. Update frontmatter: refresh `last_updated`, keep `status: executing`
5. If restart fails after 2 attempts, present:
```
Editor crashed and could not be restarted. Options:
[1] Retry restart
[2] I'll restart manually, then continue
[3] Stop and save progress (resume later with --resume)
```

### VERIFY Phase (Tasks 16-17) — Dispatch Verifier Agent

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
