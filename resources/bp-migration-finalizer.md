> Reference guide — skill methodology, not an agent definition. Loaded by skills when this workflow is needed.

# BP Migration Finalizer

Handle the SWAP and COMPLETE phases. This is the most critical phase — mistakes here affect the live Blueprint. Follow each step exactly.

## Inputs

You receive from the orchestrator:
- **migration-plan.md** — the approved plan with YAML frontmatter
- **Relevant sections of migration-plan.md** — Execution Log, Verification Results, Task List (orchestrator extracts these before dispatch)
- **Task range** — which tasks to execute (e.g., "Tasks 18-22")

## SWAP Phase Protocol

### Fast Mode Compatibility

**Detection:** Fast mode is identified by the task range prefix. Tasks prefixed with "Fast-" (e.g., Fast-14) indicate fast mode. Tasks without prefix (e.g., Task 19) indicate full mode. No separate mode flag is needed.

**In fast mode (Fast-14), execute these SWAP Phase Protocol sections:**
1. "Task: Execute Rename Swap" — full protocol (3-step rename sequence + rollback on failure)
2. "Task: Remove Orphaned Nodes (Task 19b)" — full protocol
3. "Task: Save Blueprint to Disk (Task 19c)" — full protocol
4. "Task: Fix Redirectors and Recompile Dependents" — full protocol
5. "Task: Write Final Report" — write `rollback.json` + append report to `migration-plan.md`

**Skip these sections:**
- "Task: Disable Auto-Save" — not needed (no dependents in fast mode)
- "Task: Re-Enable Auto-Save" — not needed (was never disabled)

**Changes from full mode:**
- In Final Report, report "Tasks Completed: 14/14" (not 22/22)
- Set `backup_verified` but do NOT present the backup menu — return the value to orchestrator for auto-archive

### Task: Disable Auto-Save

Disable editor auto-save before starting the swap. This prevents saving packages with unresolved redirectors mid-swap.

### Task: Execute Rename Swap

Execute the rename swap as a 3-step sequence (NOT a single batch — redirectors must be fixed between steps):
1. `rename_blueprint`: `BP_Name` -> `BP_Name_Backup`
2. `fixup_redirectors` on the parent directory — CRITICAL: this resolves the redirector left at `BP_Name`'s original location. Without this step, step 3 can fail because UE's `FAssetToolsModule` may refuse to rename to a path occupied by a redirector.
3. `rename_blueprint`: `BP_Name_Migration` -> `BP_Name`

Rollback protocol: If step 3 fails after step 1 succeeded, immediately reverse step 1:
- `rename_blueprint`: `BP_Name_Backup` -> `BP_Name`
- Report the failure to orchestrator with both the original error and the rollback status
- Do NOT leave the project in a state where `BP_Name` does not exist

**Step 2b: Verify backup exists on disk**

After rename swap completes:
1. Verify backup asset on disk (or via MCP `get_info` on backup path):
   ```bash
   ls Content/**/BP_{Name}_Backup.uasset 2>/dev/null
   ```
2. If backup exists: record in `rollback.json`:
   - `"backup_verified": true`
   - `"backup_path": "/Game/.../BP_Name_Backup"`
3. If backup does NOT exist:
   - Set `"backup_verified": false` in `rollback.json`
   - Report WARNING to orchestrator: "Backup asset not found on disk after rename swap. The original Blueprint may have been consumed by redirector resolution."
   - Orchestrator must inform the user before proceeding to COMPLETE.

**Backup status reporting:**
- Report `backup_verified` status to the orchestrator in your return summary
- The orchestrator handles the user-facing backup menu (Keep/Archive/Delete) — do NOT present backup options to the user from this agent

**Rollback tracking (record in rollback.json):**
- If first rename succeeded but second failed: reverse first rename
- If both renames succeeded but save failed: reverse both renames, save
- Record `git_commit_before` for C++ file rollback

### Task: Remove Orphaned Nodes (Task 19b)

After the rename swap succeeds, delete all orphaned nodes from migrated graphs:

1. Read the Node Mappings section from `migration-plan.md` — use the orphaned node IDs as the deletion list
2. For each graph with orphaned nodes:
   - Call `delete_orphaned_nodes` with the list of node IDs for that graph
   - Verify graph node count matches expected post-cleanup count via `graph_get_subgraph` (the default `compact=true` mode is fine here — you only need the total node count returned at the top level, which compact mode preserves)
3. Compile Blueprint — must be 0 errors, 0 warnings
4. Only proceed to Task 19c after compile succeeds

**Do NOT save before compiling.** A save of a Blueprint with errors persists corrupt state to disk.

**Order of deletion does not matter.** The underlying `RemoveNode` API breaks all pin links before destroying each node — no dangling references.

**Do NOT call `RefreshAllNodes` after deletion.** That API is for type system changes (class renames, property additions), not node removal. It can cause unexpected pin reconnection on surviving nodes.

### Task: Save Blueprint to Disk (Task 19c)

1. Call `save_blueprint` on the migrated Blueprint (now at the original path after rename swap)
2. Verify response: `saved: true`
3. Rationale: unsaved changes are lost if the editor closes unexpectedly. Save immediately after successful compile so the clean state is durable.

### Task: Fix Redirectors and Recompile Dependents

1. Identify all redirectors created by the swap
2. For each dependent Blueprint (from impact analysis):
   - Load the dependent
   - Call `RefreshAllNodes` (clears stale GUIDs from reparenting)
   - Recompile
   - Verify 0 errors
3. Delete resolved redirectors
4. Verify no remaining redirector references via AssetRegistry query

### Task: Re-Enable Auto-Save

Re-enable editor auto-save after swap is complete and all dependents are recompiled.

## COMPLETE Phase Protocol

### Task: Write Final Report

Write `rollback.json` (the ONE file that remains separate — machine-readable for automated rollback):
```json
{
  "backup_verified": true,
  "backup_path": "/Game/.../BP_Name_Backup",
  "rename_steps": [
    { "step": 1, "from": "BP_Name", "to": "BP_Name_Backup", "status": "completed" },
    { "step": "1b", "action": "fixup_redirectors", "status": "completed" },
    { "step": 2, "from": "BP_Name_Migration", "to": "BP_Name", "status": "completed" }
  ],
  "cpp_files": ["Source/.../ClassName.h", "Source/.../ClassName.cpp"],
  "git_commit_before": "{hash}"
}
```

Append final report to `migration-plan.md`. Use the Edit tool — if the `## Final Report` heading already exists, replace it; otherwise insert at the end.

Update frontmatter `status: completed`, `phase: complete`, `last_updated` as part of the same edit.

```markdown
## Final Report

| Metric | Value |
|--------|-------|
| Status | Completed |
| Duration | {time} |
| Tasks Completed | 22/22 |
| Tasks Skipped | 0 |
| Backup | {path or "not preserved"} |
| C++ Class | {ClassName} at {header_path} |

### Files Created
- `Source/{Module}/{ClassName}.h`
- `Source/{Module}/{ClassName}.cpp`

### Files Modified
- `Source/{Module}/{Module}.Build.cs` (if applicable)
- `/Game/.../{BP_Name}.uasset` (reparented)
```

Do NOT write `report.json`. The final report is inline.

## Crash Detection Protocol

Before every MCP tool call, and after any MCP error:

**Detection:**
- If MCP tool returns ConnectionError, ConnectionReset, or ConnectionRefused: **STOP IMMEDIATELY**. Do not retry. Do not work around.
- If MCP tool does not respond within 30 seconds: check whether editor PID is alive. If PID is dead, treat as crash.

**Response:**
Return to orchestrator with structured crash report:
```json
{
  "status": "editor_crashed",
  "failed_task": <task_number>,
  "last_successful_task": <task_number>,
  "error": "<connection error message>",
  "recovery_hint": "restart_editor_and_resume"
}
```

**NEVER:**
- Retry MCP calls after connection loss
- Attempt to restart the editor yourself
- Skip the failing task and continue
- Use alternative tools to work around the crash

## Recovery

If the swap fails:
- Do NOT attempt to fix it yourself
- Return the exact failure state to the orchestrator
- Include which rename step succeeded/failed
- The orchestrator will present rollback options to the user

## Output

Write:
- `docs/migration/blueprint-to-cpp/{BP_Name}/rollback.json` — rollback steps and status
- Append final report to `docs/migration/blueprint-to-cpp/{BP_Name}/migration-plan.md`

## Tools

- `rename_blueprint`
- `fixup_redirectors`
- `recompile_dependent_blueprints`
- `compile_blueprint`
- `delete_orphaned_nodes`
- `save_blueprint`
- `graph_get_subgraph`

