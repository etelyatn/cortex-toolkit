---
name: bp-migration-finalizer
description: Phase 5/6 swap, rollback, and final report assembly for migration V5
model: inherit
color: red
---

# BP Migration Finalizer

Handle Phase 5 (swap), Phase 6 (finalize), and Gate 4.

## Inputs
- `01-pre-migration.json`
- `02-migration-plan.json`
- `03-node-mapping.json`
- `04-verification.json`

## Phase 5 (Swap)
1. Ensure editor auto-save is disabled for the swap window
2. Execute rename swap sequence (original <-> migrated)
3. Run redirector fixup
4. Recompile dependent Blueprints
5. Validate level instances still resolve

## Phase 6 (Finalize)
1. Present Gate 4 options: keep / rollback / clean orphans
2. For partial migrations, update pass metadata and restart note
3. Merge all section files into canonical `report.json`

## Report Files
Write:
- `docs/migration/blueprint-to-cpp/{BP_Name}/05-rollback.json`
- `docs/migration/blueprint-to-cpp/{BP_Name}/report.json`

## Tools
- `rename_blueprint`
- `fixup_redirectors`
- `recompile_dependent_blueprints`
- `compile_blueprint`
