# Data Patterns

Common patterns for working with UE data assets via UnrealCortex MCP tools.

## Schema Discovery (fast path)

Check `.cortex/schema/_catalog.md` first for project overview, struct schemas, and table inventory. The catalog includes engine and plugin version info. If schema files are missing or stale (>24h), use `core_cmd(command="schema_status")` to check freshness, then `schema_generate` to regenerate.

```
core_cmd("schema_status") → (if stale) schema_generate → read _catalog.md → read data.md
```

When a workflow needs one deterministic schema artifact on disk for offline validation or migration tooling, use `data_cmd(command="export_schema_json")` instead of piecing together repeated `get_datatable_schema`, `get_struct_schema`, or DataAsset class reads.

## DataTable Workflows

### Create New DataTable
```
data_cmd("create_datatable") → data_cmd("add_datatable_row") (×N) OR data_cmd("import_datatable_json") → data_cmd("query_datatable") (verify)
```

**Example:**
```python
data_cmd(
    command="create_datatable",
    params={"table_path": "/Game/Data/DT_Enemies", "row_struct": "EnemyDefinition"}
)
# Then populate:
data_cmd(
    command="import_datatable_json",
    params={"table_path": "/Game/Data/DT_Enemies", "json_data": [
        {"name": "Goblin", "health": 50, "damage": 10},
        {"name": "Orc", "health": 150, "damage": 25}
    ]}
)
```

### Query and Filter
```
data_cmd("list_datatables") → data_cmd("get_datatable_schema") → data_cmd("query_datatable", params)
```

### Bulk Population
```
reflect_cmd("get_struct_schema") → prepare JSON → data_cmd("import_datatable_json") → data_cmd("query_datatable") (verify)
```

### Cross-Table Analysis
```
core_cmd("batch") (multiple tables) → correlate by shared keys (FName, tags)
```

### Large Raw Exports

For large DataTable, StringTable, or DataAsset reviews, export raw payloads to files and inspect them locally instead of returning full rows or properties through chat. File-backed Data commands return a compact summary envelope with `success`, `partial`, `warnings`, `errors`, `files_written`, `targets_touched`, and nested `counts`; use the written files for full rows, entries, properties, and per-operation details.

When exporting DataAssets with `include_properties=true`, inspect serialization status fields in the MCP response before trusting the file contents. Deep property export can now report `partial=true`, `issue_count`, and `omitted_assets`; strict mode with `allow_partial=false` can fail instead of writing a partial asset set.

```json
{
  "tool": "data_cmd",
  "command": "export_bulk_json",
  "params": {
    "out_dir": "Saved/CortexExports/DataAudit",
    "items": [
      {
        "type": "datatable",
        "name": "items",
        "table_path": "/Game/Data/DT_Items",
        "out_path": "items.json"
      },
      {
        "type": "string_table",
        "name": "item_text",
        "string_table_path": "/Game/Data/ST_ItemText",
        "out_path": "item_text.json"
      },
      {
        "type": "data_assets",
        "name": "item_assets",
        "class_name": "PrimaryDataAsset",
        "path_filter": "/Game/Data/Assets",
        "include_properties": true,
        "out_path": "item_assets.json"
      }
    ]
  }
}
```

Use individual exports when only one resource is needed:

- `export_datatable_json`
- `export_string_table_json`
- `export_data_assets_json`
- `export_schema_json`

### Snapshot Diff and Reconcile Review

When you already have two exported snapshots, use `compare_data_json` to produce a deterministic report before planning writes or presenting audit findings. This is the preferred review step for exported DataTable rows, StringTable entries, and DataAsset property snapshots.

```
export_* → inspect local files → data_cmd("compare_data_json") → inspect diff report → decide whether to stop, hand-review, or build import queue
```

**Example:**
```json
{
  "tool": "data_cmd",
  "command": "compare_data_json",
  "params": {
    "left_path": "Saved/CortexExports/Baseline/items.json",
    "right_path": "Saved/CortexExports/Proposed/items.json",
    "report_path": "Saved/CortexExports/Diff/items_diff.json",
    "mode": "data_assets",
    "ignore_fields": ["LastModified"],
    "include_equal": false
  }
}
```

Use `mode="auto"` only for canonical Cortex export wrapper shapes. Use explicit modes for top-level arrays, custom wrappers, or when you need to force DataTable rows vs StringTable entries vs DataAssets semantics.

### File-Backed Import Queues

For large, repeatable, or externally prepared write batches, prefer a queue file plus `apply_import_ops_json` over long chat-driven loops of direct mutations. This keeps write intent explicit and makes preview, apply, and verification replayable from disk.

```
export_* or export_bulk_json → inspect local files → optional export_schema_json for offline validation → optional compare_data_json → build queue JSON outside MCP → apply_import_ops_json dry_run=true → inspect report file → apply_import_ops_json dry_run=false apply=true → inspect report/query_back
```

**Example:**
```json
{
  "tool": "data_cmd",
  "command": "apply_import_ops_json",
  "params": {
    "ops_path": "Saved/CortexImports/quest_cortex_ops.json",
    "report_path": "Saved/CortexImports/quest_import_report.json",
    "dry_run": true,
    "apply": false,
    "query_back": true,
    "stop_on_error": true,
    "allow_partial": false
  }
}
```

The MCP response is only the compact summary envelope. The report file on disk is the source of truth for per-operation status, warnings, failures, partial execution state, and query-back payloads. For `apply_import_ops_json`, read aggregate execution counts from nested `counts` keys such as `operations`, `validated`, `previewed`, `attempted`, `applied`, `failed`, `skipped`, and `save_failed`.

## Asset Discovery, Search, and Read Contracts

### Search and list (project-wide)

```
data_cmd("search_assets") → data_cmd("list_data_assets", class_name=...) → data_cmd("get_data_asset")
```

`search_assets` filters with `query` (case-insensitive substring over asset name **or** object path),
`class_names` (**exact** class name, subclasses excluded) and `path_prefixes` (canonical mounted
package folders such as `/Game/Data`, recursive on folder boundaries). `fields` is a **projection**
whitelist over `path|name|class_name|package_path` (default `[path, name, class_name]`), not a filter.
It is natively paged: `offset`/`limit` (defaults `0`/`50`) slice a deterministic canonical object-path
order applied *before* paging, so pages are stable. `total_matches` is the exact filtered population
independent of the page; follow `offset = next_offset` while `is_complete == false`.
`count_only=true` returns `assets=[]`, `count=0`, exact `total_matches`, `is_complete=true` — use it
for a cheap population count. Malformed arrays/prefixes/fields refuse `INVALID_FIELD` before any
registry fetch. (The older scalar `class_filter`/`path_filter` reads and the `total_before_limit` field
are gone.)

`list_data_assets` filters with `class_name` (optional, subclass-aware) and `path_filter`. The field
was renamed from `class_filter`, which is no longer read at all — a caller still passing `class_filter`
is silently unfiltered.

`get_data_catalog` accepts `sections` (`datatables|gameplay_tags|data_assets|string_tables|curve_tables`;
omitted/empty builds every section) and `include_asset_paths` (default `false`). A missing section key
means the section was not requested; the per-class `asset_paths` inventory is only emitted when
`include_asset_paths=true`. It is reachable from both `data_cmd` and `core_cmd`.

### Targeted vs full DataAsset reads

`get_data_asset` accepts `fields`, a list of non-empty property paths. Omitted/empty keeps the previous
full deep reflected read; a non-empty list returns only those paths, keyed by the requested path
(consistent with class-default selected reads). An unresolvable path refuses
`PropertyNotFound`. `partial` and `issues` are always present (`issues` may be empty); `warnings`
appears only when package capture produced warnings.

## DataAsset Workflows

### Inspect
```
data_cmd("list_data_assets") → data_cmd("get_data_asset") → review properties
```

`get_data_asset` is a deep read. Always inspect `partial` and `issues` alongside `properties`, especially when the asset contains nested structs, instanced structs, sets, maps, or unsupported reflected property types.

### Modify
```
data_cmd("get_data_asset") → data_cmd("update_data_asset") → data_cmd("get_data_asset") (verify)
```

## GameplayTag Workflows

### Validate Before Use
```
data_cmd("validate_gameplay_tag") → data_cmd("register_gameplay_tag") (if missing) → use in data
```

### Bulk Register
```
data_cmd("register_gameplay_tags") (batch) → data_cmd("list_gameplay_tags") (verify)
```

## CurveTable Workflows

### Read Curve
```
data_cmd("list_curve_tables") → data_cmd("get_curve_table") → analyze keys
```

### Modify Curve
```
data_cmd("get_curve_table") → data_cmd("update_curve_table_row") → data_cmd("get_curve_table") (verify)
```

## Benchmark Tests

Data domain workflows are validated by the benchmark testing framework in `Plugins/UnrealCortex/MCP/tests/`:

| Test File | Coverage |
|-----------|----------|
| `test_e2e.py` | DataTable CRUD, schema queries, row operations, GameplayTag validation, CurveTable/StringTable/DataAsset ops, batch queries, search |
| `test_mcp_scenarios.py` | Data Pipeline (query + add + search + batch + delete), GameplayTag Workflow (register + validate + bulk), Localization Pipeline (get/set translations) |
| MCP benchmark Data Localization Migration check | `update_string_table` dry-run/apply workflow, preview-only operation results, `search_mode="string_table_refs"` reference scan with forwarded `limit` |
| `test_mcp_scenarios.py -k stress` | 100 rapid add/update/delete cycles, 20-command concurrent batch |

Run to validate after modifying Data MCP tools or C++ command handlers.

## Common Pitfalls

- Always verify struct schema before adding rows — field names are case-sensitive
- Use `data_cmd(command="search_assets")` to find assets by name or path when the path is unknown (project-wide); use `data_cmd(command="list_data_assets", params={"class_name": "..."})` for DataAsset-class-scoped discovery
- GameplayTags must be registered before use in DataTable rows
- `data_cmd(command="import_datatable_json")` overwrites existing rows with same key
- Use `data_cmd(command="update_string_table")` for bulk StringTable edits; run `dry_run=true` first and apply only after inspecting `operation_results`
- Use `data_cmd(command="compare_data_json")` for deterministic exported-file diffs instead of manual line-by-line review or chat-sized payload comparisons
- Use `data_cmd(command="apply_import_ops_json")` for large/repeatable write batches; preview with `dry_run=true` first, treat the compact MCP response as envelope-only status plus nested aggregate counts, and use the report file for per-operation detail
- Use `search_datatable_content` with `search_mode="string_table_refs"` before renaming/deleting StringTable keys referenced by DataTable `FText` fields
- Soft references in DataAssets must point to valid asset paths
- `get_data_asset` can succeed with `partial=true`; inspect `issues` before assuming every nested property was serialized
- `export_data_assets_json(include_properties=true)` can omit assets with blocking serialization issues; inspect `partial`, `issue_count`, and `omitted_assets`, and use `allow_partial=false` when you want strict failure instead of a partial export
