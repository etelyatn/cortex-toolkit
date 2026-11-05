> Reference guide — skill methodology, not an agent definition. Loaded by skills when this workflow is needed.

# BP Migration Verifier

Verify that the executed migration matches the approved plan. Compare the original Blueprint against the migrated copy. Verification phase — report facts, do not fix issues.

## Inputs

You receive from the orchestrator:
- **Relevant sections of migration-plan.md** — Pre-Migration Snapshot, Migration Scope, Execution Log, Node Mappings (orchestrator extracts these before dispatch — you do NOT receive the full file)
- **Task range** — which verification tasks to execute (e.g., "Tasks 16-17")

## Verification Protocol

#### Multi-Class Verification (When migration-plan.md contains `goal: redesign`)

Additional verification steps for redesign migrations:

1. **Target class existence** — verify all target classes from `target_classes` frontmatter exist in the reflection system:
   - Call `query_class_context` on each target class name
   - Confirm class exists, compiles, and has expected parent class
   - For components: verify they appear in `query_class_hierarchy` under `UActorComponent` or `USceneComponent`

2. **Component wiring** — for Tier 1, verify the primary class constructor creates all expected components:
   - Call `analyze_blueprint_for_migration` on the migrated BP
   - Check `scs_components` list: inherited C++ components should appear here
   - Verify each expected component name and class matches the Architecture Proposal
   - **Cannot verify:** `SetupAttachment` (not visible in CDO), delegate bindings (runtime only). Report these as "not statically verifiable."

3. **Responsibility coverage** — cross-reference the responsibility map:
   - Every "MIGRATING" item should have a C++ equivalent in the appropriate target class
   - Use the Ground Truth Table `Target Class` column for verification
   - Report any items in the responsibility map that lack a ground truth entry

4. **Integration point verification** — for each documented integration point:
   - Verify cached UPROPERTY pointers exist in the primary class header (grep for component type declarations)
   - Verify delegate declarations exist where specified (grep for `DECLARE_DYNAMIC_MULTICAST_DELEGATE`)
   - Verify interface implementations where specified (grep for `IInterface` in class declaration)

5. **STAYING-node rewiring report** — count STAYING nodes that reference migrated variables (from execution log):
   - If count > 0: WARNING with list of nodes requiring manual rewiring
   - If count == 0: PASS

6. **Tier 3 residual check** — if Tier 3 items exist:
   - Verify they are still present in the BP (not accidentally cleaned up)
   - Report them as "Pending manual migration" in the verification results

### Task: Structural Verification

Call `compare_blueprints` with the original and migrated Blueprint paths.

Build these comparison tables:

1. **Component inventory** — all present, none missing, none duplicated
2. **Property comparison** — pre vs post values for every migrated property
3. **Logic coverage** — every original graph node has a C++ equivalent (cross-reference with the Node Mappings section)
4. **Asset references** — meshes, materials, VFX, sounds all match
5. **Attachment hierarchy** — preserved correctly

**6. Orphaned Node Check**
For each event graph that was part of the migration:
- Count nodes that are NOT event entry nodes and NOT reachable from any event exec chain
- If count > 0: report WARNING — "N orphaned nodes remain in {graph_name}"
- If count == 0: report PASS — "No orphaned nodes in {graph_name}"

Use the node list from `analyze_blueprint_for_migration` or `graph_get_subgraph` to count remaining non-event nodes after migration. The default `compact=true` mode is sufficient here — compact preserves the `class` field used to identify event entry nodes (`UK2Node_Event` and subclasses), and only strips `node_class` (a duplicate).

### Task: Dependency Impact Check

For each public member of the original Blueprint:

| Status | Condition |
|--------|-----------|
| **SAFE** | C++ equivalent exists with same name + same signature |
| **WARNING** | C++ has same name but different signature (pins disconnect) |
| **BREAKING** | No C++ equivalent found (caller node becomes error) |

Call `analyze_blueprint_for_migration` on the migrated copy for post-migration sanity check.

**UNSAFE TOOLS — Do NOT call during mid-migration verification:**
- `compare_blueprints` — known crash vector on recently-reparented Blueprints with stale object references (Issue 99). Use individual tool calls instead (`analyze_blueprint_for_migration`, `get_class_defaults`) until Issue 99 fix is confirmed deployed.

### Task: Text Inventory Comparison

Call `blueprint_cmd(command="export_text_inventory", params={"asset_path": ..., "out_path": ...})` on the original and the migrated copy and diff the two inventories. Entries are sorted by (`location`, `owner`, `path`) so a line-by-line diff is meaningful; report every entry whose `value`, `source_kind` or `table_id`/`key` changed, was added or disappeared. The inline response is capped at 40000 characters; for anything larger pass `out_path` (under the project `Saved`, `Content` or `Config`) and read the file — without it the command returns `RESPONSE_TOO_LARGE` with the `counts` and no entries.

### Task: Snapshot Comparison

Take a snapshot before the change and another after it, then diff them. `blueprint_cmd(command="export_snapshot", params={"asset_path": ..., "out_path": ...})` writes a deterministic, sorted file (variables, CDO with the declaring class, components, widgets, bindings, animations, text, interfaces, graph entries) and answers only with `asset_path`, `out_path`, `format_version` and per-section `counts`. Pass `sections` to limit it; both snapshots of one comparison must use the same sections. `out_path` must resolve under the project `Saved`, `Content` or `Config`.

`blueprint_cmd(command="compare_snapshots", params={"before": ..., "after": ..., "report_path": ...})` is read-only and classifies every record by section and key as `added`, `removed`, `changed` or `moved`. A CDO property whose declaring class changed (for example a Blueprint variable that became a native `UPROPERTY` after reparenting) with an equal value is `moved`, not a loss — that is the expected result of a BP→C++ migration; report `changed` and `removed` entries as mismatches and `moved` entries as informational. Snapshots with different `format_version`, files that are not snapshots, identical `before`/`after` paths and sections present on one side only are refused. The inline report is limited to 40000 characters; a larger one returns `RESPONSE_TOO_LARGE` with totals and no `differences`, so pass `report_path` (a file under `Saved`, `Content` or `Config`) for anything non-trivial and read the file.

### Task: Bulk Compile Check

After the migration, `blueprint_cmd(command="compile_all", params={"path_prefix": "/Game/...", "out_path": ...})` (or `paths` — exactly one of the two, optional `types` of `Actor|Component|Widget|Interface|FunctionLibrary|Unknown`) compiles every Blueprint through the single-asset compile and writes a per-asset report. The response carries only `out_path`, `totals` (`total`, `success`, `warning`, `error`, `skipped`, `not_found`, `excluded_by_type`) and `first_failures`; read the report file for diagnostics. Report any non-zero `error` or `not_found` as a mismatch. Read-only content is skipped with a reason and level script Blueprints are not enumerated. The call is synchronous and compiles on the game thread; scope it to the migrated folder.

### Task: Redirector Check

`core_cmd(command="list_redirectors", params={"path": "/Game/...", "recursive": true})` is a read-only inventory (`redirector_path`, `destination`, `referencer_count`, `referencers`) of redirectors left in a folder. Use it after the rename swap to confirm nothing still references a stale redirector before calling `fixup_redirectors`; it fixes, deletes and saves nothing.

### Task: Placed Instance Check

`level_cmd(command="export_class_instances", params={"class": "BP_Name_or_NativeClass", "maps": ["/Game/Maps/Main"], "out_path": ...})` writes every placed instance of the class (subclasses included) from saved maps without opening them: per instance the editable properties that differ from the class default (`changed_only`, default `true`; `false` for all), with the archetype value. Run it before and after the migration and diff the two reports to find per-instance overrides that were lost. Maps that use external actor packages (One File Per Actor / World Partition) are refused rather than reported as empty. The response returns `out_path` and `totals` (`maps`, `instances`, `properties`).

### Task: Editor Turnaround

After a C++ change, `editor_cmd(command="live_coding_compile")` triggers a Live Coding patch and answers when it completes (`result`: `success`, `no_changes`, `failure`, `cancelled`, `in_progress`). It never starts Live Coding: `NOT_AVAILABLE` means no Live Coding in this build or session. Live Coding patches function bodies only — new or changed `UCLASS`/`USTRUCT`/`UPROPERTY` declarations need a full editor build and restart. After a build or restart, `editor_cmd(command="wait_ready", params={"reopen_assets": [...], "timeout": 120})` answers once GEditor is valid, the Asset Registry has loaded and no Blueprint or asset compilation is pending (`ready`, `waited_seconds`, `opened`, `failed`), or with `TIMEOUT`; `timeout` is greater than 0 and at most 3600 seconds. It never restarts the editor.

### Visual Comparison (If Applicable)

For Blueprints with visual components, capture viewport screenshots of both original and migrated copy using `capture_screenshot`. Skip for non-visual BPs.

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

## Output

Append verification results to `migration-plan.md`. Use the Edit tool — if the `## Verification Results` heading already exists (from a retry), replace it; otherwise insert at the end.

Update frontmatter `last_updated` and `phase: verify` as part of the same edit.

```markdown
## Verification Results

| Check | Result | Details |
|-------|--------|---------|
| Components | 6/6 match | All SCS components accounted for |
| Properties | 4/4 match | CDO values identical |
| Logic coverage | 12/12 mapped | All event graph nodes have C++ equivalents |
| Asset references | 3/3 match | Meshes, materials, VFX intact |
| Orphaned nodes | 0 remaining | EventGraph clean |
| Dependency impact | 0 BREAKING | No external callers affected |

### Mismatches

(none -- or list any issues found)
```

Return concise summary to orchestrator. Do NOT write `04-verification.json`.

## Tools

- `compare_blueprints`
- `analyze_blueprint_for_migration`
- `capture_screenshot`
- `get_class_defaults`
- `export_text_inventory`
- `export_snapshot`
- `compare_snapshots`
- `compile_all`
- `list_redirectors`
- `export_class_instances`
- `live_coding_compile`
- `wait_ready`

