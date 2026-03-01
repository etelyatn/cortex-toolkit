---
name: cortex-bp-migrate
description: Migrate Blueprint logic to C++, or audit a Blueprint for migration candidates. Supports --audit (analysis only) and --dry-run (generate but don't write).
---

# Blueprint to C++ Migration

Analyzes a Blueprint against existing C++ code, determines the right action (migrate, merge, improve, delete, or keep), and generates C++ code with the C++ Migration Specialist agent.

## Steps

### 1. Parse User Input

Extract:
- Blueprint path/name
- mode flag: `--audit` or `--dry-run`
- migration preferences

Check whether `docs/migration/blueprint-to-cpp/{BP_Name}/` exists and contains section files (e.g., `01-pre-migration.json`) from a previous v2 run. If it does, note this to the user and offer to resume via the `cortex-toolkit:bp-migration-planner` agent instead of starting fresh.

### 2. Dispatch Planner Agent (Phase 1)

Delegate to `cortex-toolkit:bp-migration-planner`.

The planner agent:
1. Reads project context and coding standards
2. Analyzes Blueprint via MCP
3. Scans existing C++ source
4. Classifies outcome: Migrate / Merge / Improve / Delete / Keep
5. Presents migratable elements for user selection (interactive, multiSelect)
6. Produces a migration plan and node mapping

### 3. Dispatch Executor Agent (Phases 2-6)

After the planner completes and the user confirms scope, delegate to `cortex-toolkit:bp-migration-executor`.

The executor agent:
1. Generates C++ code or patches (unless audit mode or Delete/Keep)
2. Presents analysis and code
3. Asks before writing files (unless dry-run)
4. After file write, asks user about Blueprint cleanup. Cleanup order: Reparent → Disconnect nodes → Remove functions → Remove variables → Remove SCS components (consumers before producers)
5. Merges section files into `report.json`

### 4. Review Agent Results

Review output and request adjustments before write/apply.

## Supported Blueprint Types

- **Actor Blueprints** - migrated to C++ base class (AActor or existing C++ parent subclass)
- **Widget Blueprints** - migrated to C++ UUserWidget subclass with BindWidget
- **Component Blueprints** - migrated to C++ UActorComponent/USceneComponent subclass
- **FunctionLibrary Blueprints** - migrated to C++ UBlueprintFunctionLibrary with static functions
- **Interface Blueprints** - migrated to C++ UInterface + IInterface pair

## Supported Constructs

All common Blueprint constructs are translated to C++:
- **Timelines** -> UTimelineComponent + UCurveFloat/UCurveVector/UCurveLinearColor
- **Event Dispatchers** -> DECLARE_DYNAMIC_MULTICAST_DELEGATE (0-9 params)
- **Latent Actions** -> FTimerHandle callback chains (1-2 latent) or state machine (3+)
- **Blueprint Interfaces** -> UInterface + IInterface + Execute_* calls
- **Standard flow control** -> if/else, switch, for/while loops, DoOnce, Gate, FlipFlop

## Migration Outcomes

| Outcome | What Happens |
|---|---|
| Migrate | New C++ class generated, BP reparented |
| Merge | Existing C++ class extended with BP additions |
| Improve | Existing C++ class updated with improved BP logic |
| Delete | BP identified as duplicate/garbage; deletion recommended |
| Keep | BP logic is appropriate as Blueprint |
| Extract to DataAsset | Data-heavy BP → `UPrimaryDataAsset` subclass |

## Flags

- `/cortex-bp-migrate BP_HealthPickup`
- `/cortex-bp-migrate BP_HealthPickup --audit`
- `/cortex-bp-migrate BP_HealthPickup --dry-run`
- `/cortex-bp-migrate BP_Player --include-all` - skip element selection, migrate everything
- `--skip-cleanup` — Skip Phase 7 Blueprint cleanup prompt

> **For interactive guided migration** with dependency analysis, non-destructive rename-swap, rollback support, and section-based reports that survive editor restarts, use `/cortex-bp-migrate-guided` instead.
