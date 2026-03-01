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

Prefer `create_blueprint_graph` for creating from scratch — it runs all steps atomically.
For manual step-by-step construction:
```
create_blueprint
  → add_blueprint_variable (×N)
  → graph_add_node (×N)        # Add function call nodes
  → graph_connect (×N)          # Wire execution and data flow
  → graph_set_pin_value (×N)    # Set input values on nodes
  → graph_auto_layout           # Auto-arrange node positions
  → compile_blueprint
  → save_blueprint
```

### graph_add_node — Node Class Short Names

When calling `graph_add_node` or specifying nodes in `create_blueprint_graph`, use these short names:

| Short Name | UK2Node Class | Params Required |
|-----------|--------------|-----------------|
| `Event` | `UK2Node_Event` | `{"function_name": "ClassName.FunctionName"}` e.g. `"Actor.ReceiveBeginPlay"` |
| `CustomEvent` | `UK2Node_CustomEvent` | none |
| `Self` | `UK2Node_Self` | none |
| `Knot` | `UK2Node_Knot` | none |
| `MakeArray` | `UK2Node_MakeArray` | none |
| `CallFunction` | `UK2Node_CallFunction` | `{"function_name": "ClassName.FunctionName"}` |
| `Branch` | `UK2Node_IfThenElse` | none — outputs: `True`, `False` |
| `Sequence` | `UK2Node_ExecutionSequence` | none — outputs: `then 0`, `then 1`, etc. |
| `VariableGet` | `UK2Node_VariableGet` | `{"variable_name": "X"}`, `variable_class` optional |
| `VariableSet` | `UK2Node_VariableSet` | `{"variable_name": "X"}`, `variable_class` optional |
| `Timeline` | `UK2Node_Timeline` | `{"timeline_name": "MyTimeline"}` — required, returns `TimelineNameRequired` if missing |
| `SpawnActor` | `UK2Node_SpawnActorFromClass` | none |
| `CastTo` | `UK2Node_DynamicCast` | none |
| `MacroInstance` | `UK2Node_MacroInstance` | `{"macro_path": "/Game/Path/MacroLibrary.MacroName"}` — required, returns `MacroPathRequired` if missing |
| `SwitchEnum` | `UK2Node_SwitchEnum` | none |
| `SwitchString` | `UK2Node_SwitchString` | none |
| `SwitchInteger` | `UK2Node_SwitchInteger` | none |

**Removed short names** — no longer accepted: `FunctionEntry`, `FunctionResult`, `ForEachLoop`. For ForEach loops use `CallFunction` with `function_name: "KismetArrayLibrary.Array_ForEach"`.

**Unknown short names** return an explicit error listing all valid names — there is no silent fallback to `StaticLoadClass`.

**UK2Node_Event parameter format:** `"function_name"` must be `"ClassName.FunctionName"`. The class must exist in the engine and the function must be defined on it. Invalid class or function name returns `InvalidField` error.

**Sequence node outputs:** `"then 0"`, `"then 1"` etc. (space before number, not underscore).

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

### Configure Class Defaults (CDO)
```
get_class_defaults (blueprint_path)                 ← discover all settable properties
→ set_class_defaults (blueprint_path, properties)   ← set defaults with auto-compile + auto-save
```

**Example: Configure a Character Blueprint**
```python
# 1. Discover available properties
get_class_defaults(blueprint_path="/Game/Blueprints/BP_Enemy")

# 2. Set multiple defaults in one call
set_class_defaults(
    blueprint_path="/Game/Blueprints/BP_Enemy",
    properties={
        "MaxHealth": 100.0,
        "MovementSpeed": 400.0,
        "AttackDamage": 25.0,
        "DefaultInputAction": "/Game/Input/IA_EnemyAI"
    }
)
# Returns per-property results: type, previous_value, new_value, success
# Auto-compiles and auto-saves by default
```

**Example: Read specific defaults**
```python
get_class_defaults(
    blueprint_path="/Game/Blueprints/BP_Enemy",
    properties=["MaxHealth", "MovementSpeed"]
)
```

### Configure Timeline
```
create_blueprint_graph (with Timeline node) → configure_timeline (tracks + keyframes) → compile_blueprint
```

**Example: Float track for door open animation**
```python
configure_timeline(
    asset_path="/Game/Blueprints/BP_Door",
    timeline_name="OpenTimeline",
    length=1.5,
    loop=False,
    tracks=[
        {
            "type": "float",
            "name": "OpenAmount",
            "keys": [
                {"time": 0.0, "value": 0.0},
                {"time": 0.75, "value": 0.8},
                {"time": 1.5, "value": 1.0}
            ]
        }
    ]
)
```

### Configure Component Defaults
```
create_blueprint (with parent that has components) → set_component_defaults → compile_blueprint
```

**Example: Set mesh and material on a StaticMeshActor Blueprint**
```python
set_component_defaults(
    asset_path="/Game/Blueprints/BP_Barrel",
    component_name="StaticMeshComponent0",
    properties={
        "StaticMesh": "/Game/Meshes/SM_Barrel",
        "OverrideMaterials[0]": "/Game/Materials/MI_Barrel_Rusty"
    }
)
# Returns: {"component_name": "StaticMeshComponent0", "properties_set": 2, "errors": []}
```

**Array property syntax:** `PropertyName[N]` for indexed array slots (e.g., `OverrideMaterials[0]`).

### Edit Level Script Blueprint

Level Script Blueprints live inside map packages. Use `get_level_blueprint` to obtain a synthetic path, then use it with all graph and bp commands:

```python
# 1. Get synthetic asset path
result = get_level_blueprint(map_path="/Game/Maps/TestMap")
# result["asset_path"] == "__level_bp__:/Game/Maps/TestMap"
# result["save_warning"] — reminder to use save_level, not bp.save

# 2. List graphs in the Level Blueprint
graph_list_graphs(asset_path="__level_bp__:/Game/Maps/TestMap")

# 3. Add a node to EventGraph
graph_add_node(
    asset_path="__level_bp__:/Game/Maps/TestMap",
    node_class="CustomEvent",
    graph_name="EventGraph",
    position='{"x": 200, "y": 0}'
)

# 4. Compile the Level Blueprint
compile_blueprint(asset_path="__level_bp__:/Game/Maps/TestMap")

# 5. Save — must use save_level, NOT save_blueprint
save_level(map_path="/Game/Maps/TestMap")
```

**Supported commands with `__level_bp__:` paths:**
All `graph_*` commands, `compile_blueprint`, and other `bp.*` commands.

**Not supported:** `save_blueprint` / `bp.save` — returns `LevelBlueprintSaveError`. Use `save_level` instead.

### Remove an SCS Component

Use `remove_scs_component` to delete a component from a Blueprint's Components panel (SCS). Typical use: after migrating a Blueprint-layer component to a C++ `CreateDefaultSubobject` declaration.

```python
# Remove a component by its variable name
remove_scs_component(
    asset_path="/Game/Blueprints/BP_JumpPad",
    component_name="StaticMeshComponent0",
    compile=True
)
# Returns: {"removed_component": "StaticMeshComponent0", "compiled": true, "compile_status": "UpToDate"}
```

**Child promotion:** Children of the removed node are automatically re-parented to its parent — no children are lost.

**Validation:**
- Only valid on Actor-based Blueprints (those with a SimpleConstructionScript). Component and Widget Blueprints have no SCS and return `InvalidField`.
- If `component_name` is not found in the SCS, returns `ComponentNotFound`.

**Typical post-migration workflow:**

```
compile_new_cpp_class
  → rebuild_project
  → cleanup_migration (reparent BP to new C++ class, remove migrated variables/functions)
  → remove_scs_component (for each component now declared in C++ constructor)
  → compile_blueprint
```

### Review Blueprint
```
get_blueprint_info → graph_list_graphs → graph_list_nodes (per graph) → assess complexity
```

### Modify Existing Blueprint
```
get_blueprint_info → add/remove variables/functions → compile_blueprint → save_blueprint
```

## Benchmark Tests

Blueprint MCP workflows are validated by the benchmark testing framework in `Plugins/UnrealCortex/MCP/tests/`:

| Test File | Coverage |
|-----------|----------|
| `test_e2e.py` | Blueprint CRUD lifecycle, variable/function ops, compilation, error cases |
| `test_mcp_scenarios.py` | Blueprint Lifecycle scenario (create + structure + graph wiring + compile) |
| `test_blueprint_composites.py` | `create_blueprint_graph` composite tool end-to-end |
| `test_class_defaults.py` | CDO get/set with auto-compile and auto-save |

Run to validate after modifying Blueprint MCP tools or C++ command handlers.
