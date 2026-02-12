---
name: cortex-data-review
description: Use when reviewing DataTables or DataAssets for balance issues, naming convention violations, structural problems, or data integrity checks
---

# Data Review

Reviews DataTables, DataAssets, and related data for quality and balance issues.

## Before Starting

Read `.cortex/domains/data.md` for project-specific table schemas, balance rules, and naming conventions.

## Steps

### 1. Discover Data Assets

Use `get_data_catalog` for a project overview, or target specific assets:
- `list_datatables` — all DataTables with row counts
- `list_data_assets` — all DataAssets by type
- `list_curve_tables` — all CurveTables
- `list_string_tables` — all StringTables

### 2. Check Naming Conventions

Verify assets follow project naming patterns from `.cortex/domains/data.md`:
- DataTables: `DT_{SystemName}`
- DataAssets: `DA_{Name}`
- CurveTables: `CT_{Name}`
- StringTables: `ST_{Name}`

### 3. Review Structure

For each DataTable:
- `get_datatable_schema` — verify struct fields match design
- `query_datatable` — sample rows to check data quality
- Check for empty required fields, outlier values, orphaned references

For DataAssets:
- `get_data_asset` — verify all properties are populated
- Check soft references resolve to existing assets

### 4. Balance Analysis

If `.cortex/domains/data.md` defines balance rules:
- Cross-reference tables (e.g., quest rewards vs level brackets)
- Check progression curves via `get_curve_table`
- Validate GameplayTags used in data: `validate_gameplay_tag`
- Flag values outside expected ranges

### 5. Report Findings

Group by severity:
- **Errors:** Missing data, broken references, invalid tags
- **Warnings:** Naming violations, potential balance issues
- **Info:** Suggestions for improvement

Include specific row names and field values for each finding.
