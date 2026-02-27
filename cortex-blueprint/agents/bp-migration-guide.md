---
name: bp-migration-guide
description: DEPRECATED — Use cortex-bp-migrate-guided (v2.0) or the phase-based agents directly
model: inherit
color: green
---

# Blueprint Migration Guide (Deprecated)

> **This agent is deprecated.** Use the v2.0 workflow instead.

## Use Instead

For interactive guided migration: invoke `/cortex-bp-migrate-guided`

For direct phase invocation:
- **Analysis:** `bp-migration-analyst` agent
- **Execution:** `bp-migration-executor` agent
- **Verification:** `bp-migration-verifier` agent
- **Finalization (swap + report):** `bp-migration-finalizer` agent

## What Changed in v2.0

- **Non-destructive swap:** Blueprint renamed to `_Backup`, not deleted; rollback is `bp.rename` away
- **Section-based reports:** Each phase writes a JSON file (`01-pre-migration.json` through `report.json`) so migrations survive editor restarts and can resume mid-phase
- **Structural verification:** `compare_blueprints` MCP tool diffs original vs migrated Blueprint before the swap
- **Partial migration:** `--partial` flag migrates one functional group at a time; subsequent passes add more

Report files are written to `docs/migration/blueprint-to-cpp/{BP_Name}/`.
