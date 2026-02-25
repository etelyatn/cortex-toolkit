# Data Patterns

Common patterns for working with UE data assets via UnrealCortex MCP tools.

## Schema Discovery (fast path)

Check `.cortex/schema/_catalog.md` first for project overview, struct schemas, and table inventory. The catalog includes engine and plugin version info. If schema files are missing or stale (>24h), use `schema_status` to check freshness, then `generate_project_schema` to regenerate.

```
schema_status → (if stale) generate_project_schema → read _catalog.md → read data.md
```

## DataTable Workflows

### Query and Filter
```
list_datatables → get_datatable_schema → query_datatable (with filters)
```

### Bulk Population
```
get_struct_schema → prepare JSON → import_datatable_json → query_datatable (verify)
```

### Cross-Table Analysis
```
batch_query (multiple tables) → correlate by shared keys (FName, tags)
```

## DataAsset Workflows

### Inspect
```
list_data_assets → get_data_asset (specific) → review properties
```

### Modify
```
get_data_asset → update_data_asset (specific fields) → get_data_asset (verify)
```

## GameplayTag Workflows

### Validate Before Use
```
validate_gameplay_tag → register_gameplay_tag (if missing) → use in data
```

### Bulk Register
```
register_gameplay_tags (batch) → list_gameplay_tags (verify)
```

## CurveTable Workflows

### Read Curve
```
list_curve_tables → get_curve_table (specific) → analyze keys
```

### Modify Curve
```
get_curve_table → update_curve_table_row (modify keys) → get_curve_table (verify)
```

## Benchmark Tests

Data domain workflows are validated by the benchmark testing framework in `Plugins/UnrealCortex/MCP/tests/`:

| Test File | Coverage |
|-----------|----------|
| `test_e2e.py` | DataTable CRUD, schema queries, row operations, GameplayTag validation, CurveTable/StringTable/DataAsset ops, batch queries, search |
| `test_mcp_scenarios.py` | Data Pipeline (query + add + search + batch + delete), GameplayTag Workflow (register + validate + bulk), Localization Pipeline (get/set translations) |
| `test_mcp_scenarios.py -k stress` | 100 rapid add/update/delete cycles, 20-command concurrent batch |

Run to validate after modifying Data MCP tools or C++ command handlers.

## Common Pitfalls

- Always verify struct schema before adding rows — field names are case-sensitive
- Use `search_assets` to find assets by name when path is unknown
- GameplayTags must be registered before use in DataTable rows
- `import_datatable_json` overwrites existing rows with same key
- Soft references in DataAssets must point to valid asset paths
