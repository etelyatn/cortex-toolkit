---
name: cortex-data
description: Use when creating, populating, or reviewing DataTables, DataAssets, CurveTables, or StringTables — including balance and integrity checks
---

# cortex-data

Creates, populates, and reviews data assets using the Data Architect and Data Balancer agents.

## Mode Detection

Determine mode from user intent:

- **Create/Modify**: User wants to build or change data assets
  Examples: "create a DataTable", "add rows to DT_Weapons", "import data from CSV", "create a CurveTable for level XP", "rename StringTable keys", "migrate localized text references", "apply a file-backed import plan", "run a migration queue"
  → Launch `cortex-toolkit:data-architect` agent with `max_turns: 25`

- **Review/Balance**: User wants to audit, analyze, or validate existing data
  Examples: "review DT_WeaponStats for balance issues", "check XP curve", "are quest rewards fair?", "validate data integrity", "analyze item pricing"
  → Launch `cortex-toolkit:data-balancer` agent with `max_turns: 15`

- **Ambiguous** → Default to Review (read-only, safe)

## Agent Routing

| Mode | Agent | max_turns |
|------|-------|-----------|
| Create/Modify | cortex-toolkit:data-architect | 25 |
| Review/Balance | cortex-toolkit:data-balancer | 15 |

## Steps

### 1. Launch Agent

Use the Task tool with the appropriate `subagent_type` and `max_turns` for the detected mode.

**For Create/Modify**, pass the full specification:

```
Create/populate the following data asset:

**Asset type:** [DataTable | DataAsset | CurveTable | StringTable]
**Name and path:** [e.g. DT_WeaponStats at /Game/Data/]
**Struct/schema:** [field names and types, e.g. Name (FString), Damage (float)]
**Initial data:** [rows, values, or translations to populate]
**GameplayTags:** [any tags that need registration]
**Localization:** [StringTable keys or table-backed FText references to add/migrate, if relevant]
**Migration inputs:** [optional exported JSON files, queue JSON path, report path, or external planning artifacts]

WORKFLOW:
1. Read `.cortex/domains/data.md` for project conventions, existing schemas, and balance rules
2. Check `.cortex/schema/_catalog.md` for existing assets to avoid duplicates
3. Register any required GameplayTags before use
4. Choose read/write path by scope:
   - small targeted edits: use direct commands such as data_cmd(command="add_datatable_row"), data_cmd(command="update_datatable_row"), data_cmd(command="update_string_table"), or data_cmd(command="update_data_asset")
   - offline schema validation or migration-planning inputs: prefer data_cmd(command="export_schema_json") so agents/scripts can work from one deterministic schema artifact on disk
   - reconcile, audit, or migration planning from exported files: prefer the file-backed review workflow with raw exports plus data_cmd(command="compare_data_json")
   - large/repeatable migrations or externally planned batches: prefer the file-backed workflow with raw exports, optional compare_data_json review, then data_cmd(command="apply_import_ops_json")
5. If using the file-backed workflow, export and inspect large source payloads locally first, then use data_cmd(command="compare_data_json") when you need a deterministic diff between two exported snapshots before building or applying write operations
6. For direct bulk localization edits, use data_cmd(command="update_string_table") with explicit dry_run=true first, inspect operation_results, then apply the same ordered operations
7. For file-backed imports, run data_cmd(command="apply_import_ops_json") with dry_run=true first, inspect the report file, and only perform a real apply after explicit user intent with dry_run=false and apply=true. Treat the MCP response as a compact envelope plus nested aggregate `counts`, not as the per-operation source of truth
8. For table-backed FText migrations, audit references with data_cmd(command="search_datatable_content", params={"search_mode":"string_table_refs", ...})
9. Validate structure and data integrity, using compare_data_json for exported snapshot diffs and query-back plus the report file as the source of truth for file-backed imports
```

**For Review/Balance**, pass the review scope and focus:

```
Review the following data:

**Scope:** [specific asset paths, or "all DataTables in /Game/Data/"]
**Concerns:** [balance, naming, structure, data integrity, GameplayTag validity]

WORKFLOW:
1. Read `.cortex/domains/data.md` for table schemas, balance rules, and acceptable ranges
2. Discover relevant data assets via data_cmd(command="list_datatables") etc.
3. Extract small data via data_cmd(command="query_datatable"), data_cmd(command="get_curve_table")
   For large DataTable, StringTable, or DataAsset reviews, first use data_cmd(command="export_datatable_json"), data_cmd(command="export_string_table_json"), data_cmd(command="export_data_assets_json"), or data_cmd(command="export_bulk_json") to write raw files, then inspect those files locally instead of returning raw payloads through chat. Use data_cmd(command="compare_data_json") when you need a deterministic diff between two exported snapshots. For DataAsset deep reads and exports, explicitly inspect `partial`, `issues`, `issue_count`, and `omitted_assets` when present.
   For offline validation inputs without raw payloads, prefer data_cmd(command="export_schema_json") and inspect the written snapshot locally.
4. Check naming conventions and structure
5. Perform balance analysis against rules defined in .cortex/domains/data.md
6. Cross-reference related tables for consistency
7. Validate GameplayTags used in rows
8. For localization reviews, use search_datatable_content with search_mode="string_table_refs" to find DataTable FText references to StringTable keys
9. Flag outliers, missing data, broken references

Return findings grouped by severity: Errors, Warnings, Info.
```

### 2. Handling Agent Results

If the agent's response includes a **Status** line:
- **completed** — present results to the user. For creates, include asset paths and row counts. For reviews, include findings grouped by severity.
- **blocked** / **partial** — surface what was done, what remains, and what blocked it. For creates, warn the user that partially created assets may need cleanup.

If the agent's response has no Status line (e.g., turn limit reached mid-response), treat as **partial** — summarize whatever the agent produced and note that the work may be incomplete.
