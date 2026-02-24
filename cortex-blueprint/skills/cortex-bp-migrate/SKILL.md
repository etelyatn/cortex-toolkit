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

### 2. Launch C++ Migration Specialist Agent

Delegate to `cortex-blueprint:cpp-migration-specialist`.

### 3. Agent Workflow (runs autonomously)

1. Read project context and coding standards
2. Analyze Blueprint via MCP
3. Scan existing C++ source
4. Classify outcome: Migrate / Merge / Improve / Delete / Keep
3.5. Present migratable elements for user selection (interactive, multiSelect)
5. Generate C++ code or patches (unless audit mode or Delete/Keep)
6. Present analysis and code
7. Ask before writing files (unless dry-run)

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

## Flags

- `/cortex-bp-migrate BP_HealthPickup`
- `/cortex-bp-migrate BP_HealthPickup --audit`
- `/cortex-bp-migrate BP_HealthPickup --dry-run`
- `/cortex-bp-migrate BP_Player --include-all` - skip element selection, migrate everything
