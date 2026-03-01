---
name: cortex-data-create
description: Use when creating new DataTables, DataAssets, CurveTables, or StringTables from a description, spec, or design document
---

# Data Create

Creates and populates data assets from specifications using the Data Architect agent.

## Steps

### 1. Launch Data Architect Agent

Use the Task tool with `subagent_type: "cortex-toolkit:data-architect"` to delegate data creation.

Pass the full specification including:
- Asset type (DataTable, DataAsset, CurveTable, StringTable)
- Name and desired path
- Struct/schema (fields and types)
- Initial data (rows, values, translations)
- Any GameplayTags that need registration

Example prompts:
- "Create DT_WeaponStats with fields: Name (String), Damage (Float), AttackSpeed (Float)"
- "Create a CurveTable for level-up XP requirements from level 1 to 50"
- "Create StringTable ST_UIText with translations for MainMenu, Settings, Quit"

### 2. Agent Workflow (runs in background)

The Data Architect agent will:
1. Read `.cortex/domains/data.md` for project conventions and existing schemas
2. Check for existing assets to avoid duplicates
3. Register any required GameplayTags
4. Create the asset (or guide for in-editor creation if needed)
5. Populate data rows/curves/translations
6. Validate structure and data integrity
7. Cross-reference with related tables if applicable

All MCP tool calls happen in the background — you won't see each individual call.

### 3. Review Agent Results

The agent returns:
- Created asset path
- Schema/structure confirmation
- Row/entry count
- Any GameplayTags registered
- Validation results

If the agent encounters issues (invalid types, missing tags, conflicts), it will report them for you to address.

## Why Use the Agent?

- **Clean conversation** — no flood of MCP tool calls
- **Context-aware design** — agent follows project naming conventions and validates against existing schemas
- **Bulk operations** — handles large datasets efficiently
- **Expandable details** — use Ctrl+O to see what the agent did if needed
