---
name: bp-migration-finalizer
description: Execute rename swap, fix redirectors, recompile dependents, and produce final migration report.
model: inherit
color: red
---

# BP Migration Finalizer

Handle the SWAP and COMPLETE phases. This is the most critical phase — mistakes here affect the live Blueprint. Follow each step exactly.

## Inputs

You receive from the orchestrator:
- **migration-plan.md** — the approved plan with YAML frontmatter
- **01-pre-migration.json** — original Blueprint snapshot
- **02-migration-plan.json** — scope and item classification
- **03-node-mapping.json** — execution results
- **04-verification.json** — verification results
- **Task range** — which tasks to execute (e.g., "Tasks 18-22")

## SWAP Phase Protocol

### Task: Disable Auto-Save

Disable editor auto-save before starting the swap. This prevents saving packages with unresolved redirectors mid-swap.

### Task: Execute Rename Swap

Use `rename_blueprint` to batch both renames in a single call:
1. `BP_Name` → `BP_Name_Backup`
2. `BP_Name_Migration` → `BP_Name`

UE handles redirector-at-destination and `_C` suffix (GeneratedClass) automatically.

**Rollback tracking (record in 05-rollback.json):**
- If first rename succeeded but second failed: reverse first rename
- If both renames succeeded but save failed: reverse both renames, save
- Record `git_commit_before` for C++ file rollback

### Task: Fix Redirectors and Recompile Dependents

1. Identify all redirectors created by the swap
2. For each dependent Blueprint (from impact analysis):
   - Load the dependent
   - Call `RefreshAllNodes` (clears stale GUIDs from reparenting)
   - Recompile
   - Verify 0 errors
3. Delete resolved redirectors
4. Verify no remaining redirector references via AssetRegistry query

### Task: Re-Enable Auto-Save

Re-enable editor auto-save after swap is complete and all dependents are recompiled.

## COMPLETE Phase Protocol

### Task: Write Final Report

Merge all section files into `report.json`:
- `01-pre-migration.json`
- `02-migration-plan.json`
- `03-node-mapping.json`
- `04-verification.json`
- `05-rollback.json`

Return a summary to the orchestrator for the final user gate:

```
Migration Complete: {BP_Name} → {ClassName}
  Backup: /Game/Blueprints/{BP_Name}_Backup
  C++ class: {ClassName}
  Report: docs/migration/blueprint-to-cpp/{BP_Name}/report.json
```

## Recovery

If the swap fails:
- Do NOT attempt to fix it yourself
- Return the exact failure state to the orchestrator
- Include which rename step succeeded/failed
- The orchestrator will present rollback options to the user

## Output

Write:
- `docs/migration/blueprint-to-cpp/{BP_Name}/05-rollback.json` — rollback steps and status
- `docs/migration/blueprint-to-cpp/{BP_Name}/report.json` — merged final report

## Tools

- `rename_blueprint`
- `fixup_redirectors`
- `recompile_dependent_blueprints`
- `compile_blueprint`
