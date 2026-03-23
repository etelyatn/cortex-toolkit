---
name: cortex-data
description: Use when creating, populating, or reviewing DataTables, DataAssets, CurveTables, or StringTables — including balance and integrity checks
---

# cortex-data

Creates, populates, and reviews data assets using the Data Architect and Data Balancer agents.

## Mode Detection

Determine mode from user intent:

- **Create/Modify**: User wants to build or change data assets
  Examples: "create a DataTable", "add rows to DT_Weapons", "import data from CSV", "create a CurveTable for level XP"
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

### 2. Handling Agent Results

If the agent's response includes a **Status** line:
- **completed** — present results to the user. For creates, include asset paths and row counts. For reviews, include findings grouped by severity.
- **blocked** / **partial** — surface what was done, what remains, and what blocked it. For creates, warn the user that partially created assets may need cleanup.

If the agent's response has no Status line (e.g., turn limit reached mid-response), treat as **partial** — summarize whatever the agent produced and note that the work may be incomplete.
