# Blueprint Patterns

Best practices and patterns for Blueprint development with UnrealCortex.

## Blueprint Types

| Type | Use When | Parent Class |
|------|----------|--------------|
| Actor Blueprint | Placeable entity in the world | `AActor` or custom base |
| Component Blueprint | Reusable behavior attached to actors | `UActorComponent` |
| Function Library | Static utility functions | `UBlueprintFunctionLibrary` |
| Interface | Shared contract between unrelated classes | `UInterface` |
| Widget Blueprint | UI screen or component | `UUserWidget` |

## Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Actor | `BP_{Category}_{Name}` | `BP_Pickup_HealthPotion` |
| Component | `BPC_{Name}` | `BPC_InventoryManager` |
| Function Library | `BPFL_{Name}` | `BPFL_MathUtils` |
| Interface | `BPI_{Name}` | `BPI_Interactable` |
| Widget | `WBP_{ScreenName}` | `WBP_MainMenu` |

## Variable Best Practices

- Assign categories: Gameplay, Config, State, Internal
- Mark designer-tunable variables as `Exposed`
- Use meaningful names, not `NewVar_0`
- Group related variables into structs when >5 related fields

## Graph Complexity Guidelines

| Node Count | Action |
|-----------|--------|
| 1-20 | Fine as-is |
| 20-50 | Consider splitting into functions |
| 50+ | Must split — too complex for single graph |
| 100+ | Consider C++ migration for core logic |

## MCP Tool Workflows

### Create Blueprint with Structure
```
create_blueprint → add_blueprint_variable (×N) → add_blueprint_function (×N) → compile_blueprint → save_blueprint
```

### Review Blueprint
```
get_blueprint_info → graph_list_graphs → graph_list_nodes (per graph) → assess complexity
```

### Modify Existing Blueprint
```
get_blueprint_info → add/remove variables/functions → compile_blueprint → save_blueprint
```
