---
name: cortex-data
description: Use when creating, populating, or reviewing DataTables, DataAssets, CurveTables, or StringTables — including balance and integrity checks
---

# cortex-data

Creates, populates, and reviews data assets following the `resources/data-architecture.md` and `resources/data-balancing.md` guides.

## Mode Detection

Determine mode from user intent:

- **Create/Modify**: User wants to build or change data assets
  Examples: "create a DataTable", "add rows to DT_Weapons", "import data from CSV", "create a CurveTable for level XP"
  → Follow the `resources/data-architecture.md` guide.

- **Review/Balance**: User wants to audit, analyze, or validate existing data
  Examples: "review DT_WeaponStats for balance issues", "check XP curve", "are quest rewards fair?", "validate data integrity", "analyze item pricing"
  → Follow the `resources/data-balancing.md` guide.

- **Ambiguous** → Default to Review (read-only, safe)

## Routing

| Mode | Guide |
|------|-------|
| Create/Modify | `data-architecture` |
| Review/Balance | `data-balancing` |

## Steps

### 1. Execute the Workflow

Read the guide listed in the routing table for the detected mode, then execute its workflow directly in this conversation using the MCP tools it references.

**For Create/Modify**, pass the full specification:

```
Create/populate the following data asset:

**Asset type:** [DataTable | DataAsset | CurveTable | StringTable]
**Name and path:** [e.g. DT_WeaponStats at /Game/Data/]
**Struct/schema:** [field names and types, e.g. Name (FString), Damage (float)]
**Initial data:** [rows, values, or translations to populate]
**GameplayTags:** [any tags that need registration]

WORKFLOW:
1. Read `.cortex/domains/data.md` for project conventions, existing schemas, and balance rules
2. Check `.cortex/schema/_catalog.md` for existing assets to avoid duplicates
3. Register any required GameplayTags before use
4. Create the asset via data_cmd(command="create_datatable") or equivalent
5. Populate via data_cmd(command="add_datatable_row") or data_cmd(command="import_datatable_json")
6. Validate structure and data integrity
```

**For Review/Balance**, pass the review scope and focus:

```
Review the following data:

**Scope:** [specific asset paths, or "all DataTables in /Game/Data/"]
**Concerns:** [balance, naming, structure, data integrity, GameplayTag validity]

WORKFLOW:
1. Read `.cortex/domains/data.md` for table schemas, balance rules, and acceptable ranges
2. Discover relevant data assets via data_cmd(command="list_datatables") etc.
3. Extract data via data_cmd(command="query_datatable"), data_cmd(command="get_curve_table")
4. Check naming conventions and structure
5. Perform balance analysis against rules defined in .cortex/domains/data.md
6. Cross-reference related tables for consistency
7. Validate GameplayTags used in rows
8. Flag outliers, missing data, broken references

Return findings grouped by severity: Errors, Warnings, Info.
```

### 2. Reporting Results

Report results to the user with a completion status:
- **completed** — present results. For creates, include asset paths and row counts. For reviews, include findings grouped by severity.
- **blocked** / **partial** — surface what was done, what remains, and what blocked it. For creates, warn the user that partially created assets may need cleanup.

If the work is interrupted mid-execution, treat it as **partial** — summarize what was produced and note that the work may be incomplete.
