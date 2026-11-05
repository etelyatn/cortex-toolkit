> Reference guide — skill methodology, not an agent definition. Loaded by skills when this workflow is needed.

# BP Migration Finalizer

Handle the FINALIZE and COMPLETE phases. The migrated Blueprint is the original asset, migrated in place, so nothing is renamed or swapped and every referencer keeps pointing at it. This phase makes the clean state durable and leaves the project consistent. Follow each step exactly.

**Never rename, move or replace `BP_Name`.** Renaming an asset rewrites every referencer to the new path (`IAssetTools::RenameAssets` → `FAssetRenameManager::FixReferencesAndRename`), so the old rename-swap moved the whole project onto the backup. See "In-Place Migration Model" in the cortex-bp-migrate skill.

## Inputs

You receive from the orchestrator:
- **migration-plan.md** — the approved plan with YAML frontmatter
- **Relevant sections of migration-plan.md** — Execution Log, Verification Results, Task List (orchestrator extracts these before dispatch)
- **Task range** — which tasks to execute (e.g., "Tasks 18-21")

## FINALIZE Phase Protocol

### Fast Mode Compatibility

**Detection:** Fast mode is identified by the task range prefix. Tasks prefixed with "Fast-" (e.g., Fast-14) indicate fast mode. Tasks without prefix (e.g., Task 19) indicate full mode. No separate mode flag is needed.

**In fast mode (Fast-14), execute these sections in order:**
1. "Task: Final Orphan Sweep and Clean Compile (Task 18)" — full protocol
2. "Task: Save Blueprint to Disk (Task 19)" — full protocol
3. "Task: Recompile Dependent Blueprints (Task 20)" — full protocol
4. "Task: Write Final Report (Task 21)" — write `rollback.json` + append report to `migration-plan.md`

**Changes from full mode:**
- In Final Report, report "Tasks Completed: 14/14" (not 21/21)
- Set `backup_verified` but do NOT present the backup menu — return the value to orchestrator for auto-archive

### Task: Final Orphan Sweep and Clean Compile (Task 18)

Delete orphaned nodes that remain in the migrated graphs, then prove the Blueprint compiles clean:

1. Read the Node Mappings section from `migration-plan.md` and the execution log; the migrated graphs are the ones whose events were disconnected.
2. For each such graph, call `blueprint_cmd(command="delete_orphaned_nodes", params={"asset_path": "/Game/.../BP_Name", "graph_name": "..."})`. It is idempotent: a graph with nothing orphaned reports zero deletions.
3. Verify the remaining node count per graph with `graph_cmd(command="search_nodes", params={"asset_path": "...", "graph_name": "..."})` (no filter, compact rows). `blueprint_cmd` `graph_metrics` must report no `unreachable` nodes for the migrated graphs.
4. Compile: `blueprint_cmd(command="compile", params={"asset_path": "/Game/.../BP_Name"})` — must be 0 errors, 0 warnings.
5. Only proceed to Task 19 after the compile succeeds.

**Do NOT save before compiling.** A save of a Blueprint with errors persists corrupt state to disk.

**Order of deletion does not matter.** The underlying `RemoveNode` API breaks all pin links before destroying each node — no dangling references.

**Do NOT call `RefreshAllNodes` after deletion.** That API is for type system changes (class renames, property additions), not node removal. It can cause unexpected pin reconnection on surviving nodes.

### Task: Save Blueprint to Disk (Task 19)

1. Call `blueprint_cmd(command="save", params={"asset_path": "/Game/.../BP_Name"})` on the migrated Blueprint (still at its original path)
2. Verify response: `saved: true`
3. Tell the orchestrator the asset is now persisted so it sets `asset_persisted: true` if an earlier task did not already.
4. Rationale: unsaved changes are lost if the editor closes unexpectedly. Save immediately after a successful compile so the clean state is durable. This is the only deliberate save in the pipeline.

### Task: Recompile Dependent Blueprints (Task 20)

Reparenting changes the class layout, so Blueprints that depend on `BP_Name` can hold stale data.

1. Call `blueprint_cmd(command="recompile_dependents", params={"asset_path": "/Game/.../BP_Name"})`
2. Verify every dependent reports `status: success`. A dependent that fails is reported to the orchestrator with its `errors`; do not edit it.
3. There is no redirector cleanup: nothing was renamed, so no redirector was created by this migration. Do not call `fixup_redirectors` here.

**Backup verification (before returning):** confirm the snapshot exists with `blueprint_cmd(command="get_info", params={"asset_path": "<backup_path>"})`.
- If it exists: record `"backup_verified": true` and `"backup_path": "/Game/.../BP_Name_Backup"` in `rollback.json`.
- If it does not exist: record `"backup_verified": false` and report WARNING to the orchestrator: "No backup snapshot exists. The original can only be recovered from source control." The orchestrator informs the user before COMPLETE.

**Backup status reporting:** report `backup_verified` to the orchestrator in your return summary. The orchestrator handles the user-facing backup menu (Keep/Archive/Delete) — do NOT present backup options to the user from this phase, and never modify the backup.

## COMPLETE Phase Protocol

### Task: Write Final Report (Task 21)

Write `rollback.json` (the ONE file that remains separate — machine-readable for rollback):
```json
{
  "blueprint": "/Game/.../BP_Name",
  "asset_persisted": true,
  "backup_verified": true,
  "backup_path": "/Game/.../BP_Name_Backup",
  "restore": {
    "while_unpersisted": "core_cmd reload_asset on blueprint",
    "after_persisted": "restore the .uasset from source control at git_commit_before, then core_cmd reload_asset"
  },
  "cpp_files": ["Source/.../ClassName.h", "Source/.../ClassName.cpp"],
  "git_commit_before": "{hash}"
}
```

`rollback.json` never lists rename steps; the original path is unchanged. The backup is a comparison snapshot, not a restore source.

Append final report to `migration-plan.md`. Use the Edit tool — if the `## Final Report` heading already exists, replace it; otherwise insert at the end.

Update frontmatter `status: completed`, `phase: complete`, `last_updated` as part of the same edit.

```markdown
## Final Report

| Metric | Value |
|--------|-------|
| Status | Completed |
| Duration | {time} |
| Tasks Completed | 21/21 |
| Tasks Skipped | 0 |
| Backup | {path or "not preserved"} |
| C++ Class | {ClassName} at {header_path} |

### Files Created
- `Source/{Module}/{ClassName}.h`
- `Source/{Module}/{ClassName}.cpp`

### Files Modified
- `Source/{Module}/{Module}.Build.cs` (if applicable)
- `/Game/.../{BP_Name}.uasset` (reparented in place)
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

If a finalize task fails:
- Do NOT attempt to fix it yourself
- Return the exact failure state to the orchestrator, including which task failed and whether the compile or the save was the last step that succeeded
- The orchestrator will present options and, if the user wants to undo, applies the In-Place Migration Model rollback (`reload_asset` while unpersisted, otherwise a confirmed source-control restore)
- A failed or interrupted save leaves the previous on-disk state; Task 18 is idempotent and Tasks 19 and 20 are safe to re-run

## Output

Write:
- `docs/migration/blueprint-to-cpp/{BP_Name}/rollback.json` — restore information
- Append final report to `docs/migration/blueprint-to-cpp/{BP_Name}/migration-plan.md`

## Tools

- `blueprint_cmd` `delete_orphaned_nodes`, `compile`, `save`, `recompile_dependents`, `get_info`, `graph_metrics`
- `graph_cmd` `search_nodes`
