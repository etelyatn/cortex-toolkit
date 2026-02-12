---
name: cortex-data-create
description: Use when creating new DataTables, DataAssets, CurveTables, or StringTables from a description, spec, or design document
---

# Data Create

Creates and populates data assets from specifications.

## Before Starting

Read `.cortex/domains/data.md` for project naming conventions and existing table schemas.

## Steps

### 1. Understand the Spec

Parse the user's description to determine:
- Asset type (DataTable, DataAsset, CurveTable, StringTable)
- Name (following project conventions)
- Struct/schema (fields, types)
- Initial data (rows, values)

### 2. Check for Existing Assets

Use `search_assets` and `list_datatables` to verify the asset doesn't already exist.

### 3. Register GameplayTags

If the data uses GameplayTags, register them first:
- `validate_gameplay_tag` to check if tag exists
- `register_gameplay_tag` or `register_gameplay_tags` to create new ones

### 4. Create the Asset

Currently, DataTables and CurveTables are created in UE Editor (not via MCP).
Guide the user to create the asset in-editor, then populate it.

### 5. Populate Data

For DataTables:
- `add_datatable_row` for each row
- Verify with `query_datatable` after adding

For CurveTables:
- `update_curve_table_row` to set curve keys

For StringTables:
- `set_translation` for each string entry

For bulk data:
- `import_datatable_json` for large datasets

### 6. Validate

- `get_datatable_schema` to verify structure
- `query_datatable` to verify populated data
- `validate_gameplay_tag` for any tags used
- Cross-reference with related tables if applicable
