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
blueprint_cmd(command="create_blueprint", params={
    "name": "BP_SpecializedActor",
    "path": "/Game/Blueprints",
    "parent_class": "MyGameActor"  # Resolves to project's C++ class
})
```

**Full class path (for disambiguation):**
```python
blueprint_cmd(command="create_blueprint", params={
    "name": "BP_SpecializedActor",
    "path": "/Game/Blueprints",
    "parent_class": "/Script/MyGame.MyGameActor"
})
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
blueprint_cmd(command="create_blueprint", params={
    "name": "BP_CustomEnemy",
    "path": "/Game/Blueprints/Enemies",
    "parent_class": "AEnemyBase"  # Your C++ base class
})
# Returns: {"asset_path": "/Game/Blueprints/Enemies/BP_CustomEnemy", "parent_class": "EnemyBase", "type": "Actor"}

# Add Blueprint-specific variables
blueprint_cmd(command="add_blueprint_variable", params={
    "asset_path": "/Game/Blueprints/Enemies/BP_CustomEnemy",
    "name": "PatrolRadius",
    "type": "float",
    "default_value": "500.0",
    "category": "AI"
})

# Compile and save
blueprint_cmd(command="compile_blueprint", params={"asset_path": "/Game/Blueprints/Enemies/BP_CustomEnemy"})
blueprint_cmd(command="save_blueprint", params={"asset_path": "/Game/Blueprints/Enemies/BP_CustomEnemy"})
```

**Why use custom C++ parents:**
- Inherit optimized C++ logic (tick functions, collision handling, networking)
- Blueprint only adds designer-tunable overrides (patrol radius, visual mesh, sounds)
- Best of both worlds: performance + iteration speed

### Create Blueprint with Structure
```
blueprint_cmd(create_blueprint) → blueprint_cmd(add_blueprint_variable) ×N → blueprint_cmd(add_blueprint_function) ×N → blueprint_cmd(compile_blueprint) → blueprint_cmd(save_blueprint)
```

### Create Fully Functional Blueprint (Automated)

Prefer `blueprint_compose` for creating from scratch — it runs all steps atomically.
For manual step-by-step construction:
```
blueprint_cmd(create_blueprint)
  → blueprint_cmd(add_blueprint_variable) ×N
  → blueprint_cmd(graph_add_node) ×N        # Add function call nodes
  → blueprint_cmd(graph_connect) ×N          # Wire execution and data flow
  → blueprint_cmd(graph_set_pin_value) ×N    # Set input values on nodes
  → blueprint_cmd(graph_auto_layout)         # Auto-arrange node positions
  → blueprint_cmd(compile_blueprint)
  → blueprint_cmd(save_blueprint)
```

### graph_add_node — Node Class Short Names

When calling `blueprint_cmd(command="graph_add_node")` or specifying nodes in `blueprint_compose`, use these short names:

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
blueprint_cmd(command="create_blueprint", params={"name": "BP_HelloWorld", "path": "/Game/Blueprints", "type": "Actor"})

# 2. Add Delay node
blueprint_cmd(command="graph_add_node", params={
    "asset_path": "/Game/Blueprints/BP_HelloWorld",
    "node_class": "CallFunction",
    "params": {"function_name": "KismetSystemLibrary.Delay"},
    "position": {"x": 300, "y": 0}
})
# Returns: {"node_id": "K2Node_CallFunction_0"}

# 3. Add Print String node
blueprint_cmd(command="graph_add_node", params={
    "asset_path": "/Game/Blueprints/BP_HelloWorld",
    "node_class": "CallFunction",
    "params": {"function_name": "KismetSystemLibrary.PrintString"},
    "position": {"x": 600, "y": 0}
})
# Returns: {"node_id": "K2Node_CallFunction_1"}

# 4. Connect nodes: BeginPlay → Delay → PrintString
blueprint_cmd(command="graph_connect", params={
    "asset_path": "/Game/Blueprints/BP_HelloWorld",
    "source_node": "K2Node_Event_0", "source_pin": "then",
    "target_node": "K2Node_CallFunction_0", "target_pin": "execute"
})

blueprint_cmd(command="graph_connect", params={
    "asset_path": "/Game/Blueprints/BP_HelloWorld",
    "source_node": "K2Node_CallFunction_0", "source_pin": "then",
    "target_node": "K2Node_CallFunction_1", "target_pin": "execute"
})

# 5. Set input values (makes Blueprint functional!)
blueprint_cmd(command="graph_set_pin_value", params={
    "asset_path": "/Game/Blueprints/BP_HelloWorld",
    "node_id": "K2Node_CallFunction_0",
    "pin_name": "Duration",
    "value": "5.0"
})

blueprint_cmd(command="graph_set_pin_value", params={
    "asset_path": "/Game/Blueprints/BP_HelloWorld",
    "node_id": "K2Node_CallFunction_1",
    "pin_name": "InString",
    "value": "Hello World"
})

# 6. Compile and save
blueprint_cmd(command="compile_blueprint", params={"asset_path": "/Game/Blueprints/BP_HelloWorld"})
blueprint_cmd(command="save_blueprint", params={"asset_path": "/Game/Blueprints/BP_HelloWorld"})
```

**Result:** Fully functional Blueprint that prints "Hello World" 5 seconds after BeginPlay — no manual editing required!

### Configure Class Defaults (CDO)
```
blueprint_cmd(get_class_defaults, blueprint_path)                 ← discover all settable properties
→ blueprint_cmd(set_class_defaults, blueprint_path, properties)   ← set defaults with auto-compile + auto-save
```

**Example: Configure a Character Blueprint**
```python
# 1. Discover available properties
blueprint_cmd(command="get_class_defaults", params={"blueprint_path": "/Game/Blueprints/BP_Enemy"})

# 2. Set multiple defaults in one call
blueprint_cmd(command="set_class_defaults", params={
    "blueprint_path": "/Game/Blueprints/BP_Enemy",
    "properties": {
        "MaxHealth": 100.0,
        "MovementSpeed": 400.0,
        "AttackDamage": 25.0,
        "DefaultInputAction": "/Game/Input/IA_EnemyAI"
    }
})
# Returns per-property results: type, previous_value, new_value, success
# Auto-compiles and auto-saves by default
```

**Example: Read specific defaults**
```python
blueprint_cmd(command="get_class_defaults", params={
    "blueprint_path": "/Game/Blueprints/BP_Enemy",
    "properties": ["MaxHealth", "MovementSpeed"]
})
```

### Configure Timeline
```
blueprint_compose (with Timeline node) → blueprint_cmd(configure_timeline, tracks + keyframes) → blueprint_cmd(compile_blueprint)
```

**Example: Float track for door open animation**
```python
blueprint_cmd(command="configure_timeline", params={
    "asset_path": "/Game/Blueprints/BP_Door",
    "timeline_name": "OpenTimeline",
    "length": 1.5,
    "loop": False,
    "tracks": [
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
})
```

### Configure Component Defaults
```
blueprint_compose (with parent that has components) → blueprint_cmd(set_component_defaults) → blueprint_cmd(compile_blueprint)
```

**Example: Set mesh and material on a StaticMeshActor Blueprint**
```python
blueprint_cmd(command="set_component_defaults", params={
    "asset_path": "/Game/Blueprints/BP_Barrel",
    "component_name": "StaticMeshComponent0",
    "properties": {
        "StaticMesh": "/Game/Meshes/SM_Barrel",
        "OverrideMaterials[0]": "/Game/Materials/MI_Barrel_Rusty"
    }
})
# Returns: {"component_name": "StaticMeshComponent0", "properties_set": 2, "errors": []}
```

**Array property syntax:** `PropertyName[N]` for indexed array slots (e.g., `OverrideMaterials[0]`).

### Edit Level Script Blueprint

Level Script Blueprints live inside map packages. Use `blueprint_cmd(command="get_level_blueprint")` to obtain a synthetic path, then use it with all graph and bp commands:

```python
# 1. Get synthetic asset path
result = blueprint_cmd(command="get_level_blueprint", params={"map_path": "/Game/Maps/TestMap"})
# result["asset_path"] == "__level_bp__:/Game/Maps/TestMap"
# result["save_warning"] — reminder to use save_level, not bp.save

# 2. List graphs in the Level Blueprint
blueprint_cmd(command="graph_list_graphs", params={"asset_path": "__level_bp__:/Game/Maps/TestMap"})

# 3. Add a node to EventGraph
blueprint_cmd(command="graph_add_node", params={
    "asset_path": "__level_bp__:/Game/Maps/TestMap",
    "node_class": "CustomEvent",
    "graph_name": "EventGraph",
    "position": {"x": 200, "y": 0}
})

# 4. Compile the Level Blueprint
blueprint_cmd(command="compile_blueprint", params={"asset_path": "__level_bp__:/Game/Maps/TestMap"})

# 5. Save — must use save_level, NOT blueprint_cmd(save_blueprint)
blueprint_cmd(command="save_level", params={"map_path": "/Game/Maps/TestMap"})
```

**Supported commands with `__level_bp__:` paths:**
All `graph_*` commands, `blueprint_cmd(compile_blueprint)`, and other `blueprint_cmd` commands.

**Not supported:** `blueprint_cmd(save_blueprint)` — returns `LevelBlueprintSaveError`. Use `blueprint_cmd(command="save_level")` instead.

### Remove an SCS Component

Use `blueprint_cmd(command="remove_scs_component")` to delete a component from a Blueprint's Components panel (SCS). Typical use: after migrating a Blueprint-layer component to a C++ `CreateDefaultSubobject` declaration.

```python
# Remove a component by its variable name
blueprint_cmd(command="remove_scs_component", params={
    "asset_path": "/Game/Blueprints/BP_JumpPad",
    "component_name": "StaticMeshComponent0",
    "compile": True
})
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
  → blueprint_cmd(remove_scs_component) (for each component now declared in C++ constructor)
  → blueprint_cmd(compile_blueprint)
```

### Reparent Blueprint
```
blueprint_cmd(reparent, asset_path, new_parent) → auto-compiles
```

**Example: Migrate to C++ base class**
```python
blueprint_cmd(command="reparent", params={
    "asset_path": "/Game/Blueprints/BP_Enemy",
    "new_parent": "AEnemyBase"  # C++ class short name
})
# Returns: {"asset_path": "...", "old_parent": "Actor", "new_parent": "EnemyBase", "reparented": true}
```

**Example: Reparent to another Blueprint**
```python
blueprint_cmd(command="reparent", params={
    "asset_path": "/Game/Blueprints/BP_SpecialEnemy",
    "new_parent": "/Game/Blueprints/BP_EnemyBase"  # Blueprint asset path
})
```

**Resolution order:** Tries Blueprint asset path first, then C++ class name (full path or short name).

**Validation:**
- Returns error if Blueprint already has the specified parent
- Returns `InvalidParentClass` if the class cannot be resolved
- Returns `BlueprintNotFound` if the asset path is invalid

### Review Blueprint
```
blueprint_cmd(get_blueprint_info) → blueprint_cmd(graph_list_graphs) → blueprint_cmd(graph_list_nodes) per graph → assess complexity
```

**`get_blueprint_info` limitation:** The `functions` array only includes functions *defined on the Blueprint itself*. Inherited C++ functions (e.g. from a custom C++ base class) are **not listed**. To discover inherited C++ functions, use `query_class_detail(class_name, detail="full")` from the Reflect domain instead.

### Modify Existing Blueprint
```
blueprint_cmd(get_blueprint_info) → blueprint_cmd(add/remove variables/functions) → blueprint_cmd(compile_blueprint) → blueprint_cmd(save_blueprint)
```

## Benchmark Tests

Blueprint MCP workflows are validated by the benchmark testing framework in `Plugins/UnrealCortex/MCP/tests/`:

| Test File | Coverage |
|-----------|----------|
| `test_e2e.py` | Blueprint CRUD lifecycle, variable/function ops, compilation, error cases |
| `test_mcp_scenarios.py` | Blueprint Lifecycle scenario (create + structure + graph wiring + compile) |
| `test_blueprint_composites.py` | `blueprint_compose` composite tool end-to-end |
| `test_class_defaults.py` | CDO get/set with auto-compile and auto-save |

Run to validate after modifying Blueprint MCP tools or C++ command handlers.
