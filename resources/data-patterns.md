# Data Patterns

Common patterns for working with UE data assets via UnrealCortex MCP tools.

## Schema Discovery (fast path)

Check `.cortex/schema/_catalog.md` first for project overview, struct schemas, and table inventory. The catalog includes engine and plugin version info. If schema files are missing or stale (>24h), use `core_cmd(command="schema_status")` to check freshness, then `schema_generate` to regenerate.

```
core_cmd("schema_status") → (if stale) schema_generate → read _catalog.md → read data.md
```

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

For large DataTable, StringTable, or DataAsset reviews, export raw payloads to files and inspect them locally instead of returning full rows or properties through chat. Export commands return compact summaries with counts, output paths, byte sizes, warnings, and errors.

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

## DataAsset Workflows

### Inspect
```
data_cmd("list_data_assets") → data_cmd("get_data_asset") → review properties
```

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
- Use `core_cmd(command="search_assets")` to find assets by name when path is unknown
- GameplayTags must be registered before use in DataTable rows
- `data_cmd(command="import_datatable_json")` overwrites existing rows with same key
- Use `data_cmd(command="update_string_table")` for bulk StringTable edits; run `dry_run=true` first and apply only after inspecting `operation_results`
- Use `search_datatable_content` with `search_mode="string_table_refs"` before renaming/deleting StringTable keys referenced by DataTable `FText` fields
- Soft references in DataAssets must point to valid asset paths
