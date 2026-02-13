# Blueprint Patterns

Best practices and patterns for Blueprint development with UnrealCortex.

## Blueprint Types

| Type | Use When | Parent Class |
|------|----------|--------------|
| Actor Blueprint | Placeable entity in the world | `AActor` or custom C++ base |
| Component Blueprint | Reusable behavior attached to actors | `UActorComponent` or custom C++ base |
| Function Library | Static utility functions | `UBlueprintFunctionLibrary` |
| Interface | Shared contract between unrelated classes | `UInterface` |
| Widget Blueprint | UI screen or component | `UUserWidget` or custom C++ base |

### Creating Blueprints with Custom C++ Parents

Use the `parent_class` parameter to inherit from project-specific C++ base classes:

**Short name (recommended for project classes):**
```python
create_blueprint(
    name="BP_SpecializedActor",
    path="/Game/Blueprints",
    parent_class="MyGameActor"  # Resolves to project's C++ class
)
```

**Full class path (for disambiguation):**
```python
create_blueprint(
    name="BP_SpecializedActor",
    path="/Game/Blueprints",
    parent_class="/Script/MyGame.MyGameActor"
)
```

**Auto-detection:** Widget subclasses are automatically detected and create WidgetBlueprints. Interface and FunctionLibrary types are also inferred from parent class hierarchy.

**Common use cases:**
- Game-specific base classes: `AMyGameCharacter`, `AMyGameWeapon`, `UMyInventoryComponent`
- Engine framework classes: `AGameModeBase`, `APlayerController`, `APawn`
- Specialized components: `USceneComponent`, `UPrimitiveComponent`, `UWidgetComponent`

**When `parent_class` is provided, the `type` parameter is ignored.** The Blueprint type is inferred automatically from the parent class.

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

### Create Blueprint with Custom C++ Parent
```python
# Create Blueprint inheriting from custom C++ base class
create_blueprint(
    name="BP_CustomEnemy",
    path="/Game/Blueprints/Enemies",
    parent_class="AEnemyBase"  # Your C++ base class
)
# Returns: {"asset_path": "/Game/Blueprints/Enemies/BP_CustomEnemy", "parent_class": "EnemyBase", "type": "Actor"}

# Add Blueprint-specific variables
add_blueprint_variable(
    asset_path="/Game/Blueprints/Enemies/BP_CustomEnemy",
    name="PatrolRadius",
    type="float",
    default_value="500.0",
    category="AI"
)

# Compile and save
compile_blueprint(asset_path="/Game/Blueprints/Enemies/BP_CustomEnemy")
save_blueprint(asset_path="/Game/Blueprints/Enemies/BP_CustomEnemy")
```

**Why use custom C++ parents:**
- Inherit optimized C++ logic (tick functions, collision handling, networking)
- Blueprint only adds designer-tunable overrides (patrol radius, visual mesh, sounds)
- Best of both worlds: performance + iteration speed

### Create Blueprint with Structure
```
create_blueprint → add_blueprint_variable (×N) → add_blueprint_function (×N) → compile_blueprint → save_blueprint
```

### Create Fully Functional Blueprint (Automated)
```
create_blueprint
  → add_blueprint_variable (×N)
  → graph_add_node (×N)        # Add function call nodes
  → graph_connect (×N)          # Wire execution and data flow
  → graph_set_pin_value (×N)    # Set input values on nodes
  → compile_blueprint
  → save_blueprint
```

**Example: Hello World Blueprint**
```python
# 1. Create Actor Blueprint
create_blueprint(name="BP_HelloWorld", path="/Game/Blueprints", type="Actor")

# 2. Add Delay node
graph_add_node(
    asset_path="/Game/Blueprints/BP_HelloWorld",
    node_class="UK2Node_CallFunction",
    params={"function_name": "KismetSystemLibrary.Delay"},
    position={"x": 300, "y": 0}
)
# Returns: {"node_id": "K2Node_CallFunction_0"}

# 3. Add Print String node
graph_add_node(
    asset_path="/Game/Blueprints/BP_HelloWorld",
    node_class="UK2Node_CallFunction",
    params={"function_name": "KismetSystemLibrary.PrintString"},
    position={"x": 600, "y": 0}
)
# Returns: {"node_id": "K2Node_CallFunction_1"}

# 4. Connect nodes: BeginPlay → Delay → PrintString
graph_connect(
    asset_path="/Game/Blueprints/BP_HelloWorld",
    source_node="K2Node_Event_0", source_pin="then",
    target_node="K2Node_CallFunction_0", target_pin="execute"
)

graph_connect(
    asset_path="/Game/Blueprints/BP_HelloWorld",
    source_node="K2Node_CallFunction_0", source_pin="then",
    target_node="K2Node_CallFunction_1", target_pin="execute"
)

# 5. Set input values (makes Blueprint functional!)
graph_set_pin_value(
    asset_path="/Game/Blueprints/BP_HelloWorld",
    node_id="K2Node_CallFunction_0",
    pin_name="Duration",
    value="5.0"
)

graph_set_pin_value(
    asset_path="/Game/Blueprints/BP_HelloWorld",
    node_id="K2Node_CallFunction_1",
    pin_name="InString",
    value="Hello World"
)

# 6. Compile and save
compile_blueprint(asset_path="/Game/Blueprints/BP_HelloWorld")
save_blueprint(asset_path="/Game/Blueprints/BP_HelloWorld")
```

**Result:** Fully functional Blueprint that prints "Hello World" 5 seconds after BeginPlay — no manual editing required!

### Review Blueprint
```
get_blueprint_info → graph_list_graphs → graph_list_nodes (per graph) → assess complexity
```

### Modify Existing Blueprint
```
get_blueprint_info → add/remove variables/functions → compile_blueprint → save_blueprint
```
