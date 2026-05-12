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
blueprint_cmd(command="create", params={
    "name": "BP_SpecializedActor",
    "path": "/Game/Blueprints",
    "parent_class": "MyGameActor"  # Resolves to project's C++ class
})
```

**Full class path (for disambiguation):**
```python
blueprint_cmd(command="create", params={
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
blueprint_cmd(command="create", params={
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
blueprint_cmd(command="compile", params={"asset_path": "/Game/Blueprints/Enemies/BP_CustomEnemy"})
blueprint_cmd(command="save", params={"asset_path": "/Game/Blueprints/Enemies/BP_CustomEnemy"})
```

**Why use custom C++ parents:**
- Inherit optimized C++ logic (tick functions, collision handling, networking)
- Blueprint only adds designer-tunable overrides (patrol radius, visual mesh, sounds)
- Best of both worlds: performance + iteration speed

### Create Blueprint with Structure
```
blueprint_cmd(command="create") -> blueprint_cmd(command="add_variable") xN -> blueprint_cmd(command="add_function") xN -> blueprint_cmd(command="compile") -> blueprint_cmd(command="save")
```

### Create Fully Functional Blueprint (Automated)

Prefer `blueprint_compose` for creating from scratch — it runs all steps atomically.
For manual step-by-step construction:
```
blueprint_cmd(command="create")
  -> blueprint_cmd(command="add_variable") xN
  -> blueprint_cmd(command="graph_add_node") xN        # Add function call nodes
  -> blueprint_cmd(command="graph_connect") xN         # Wire execution and data flow
  -> blueprint_cmd(command="graph_set_pin_value") xN   # Set input values on nodes
  -> blueprint_cmd(command="graph_auto_layout")        # Auto-arrange node positions
  -> blueprint_cmd(command="compile")
  -> blueprint_cmd(command="save")
```

Before editing an existing graph, call `graph_cmd(command="list_graphs")` and check
the returned top-level `kind`. Delegate graphs are readable but not mutable through
generic graph edit commands. Interface implementation graphs are mutable.

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
| `AddDelegate` / `BindEvent` | `UK2Node_AddDelegate` | `{"delegate_name": "OnTakeAnyDamage", "delegate_class": "Actor"}` — `delegate_class` optional (omit for self-context). Pins: execute, then, self (Target), Delegate (Event) |
| `RemoveDelegate` / `UnbindEvent` | `UK2Node_RemoveDelegate` | same as AddDelegate. Pins: execute, then, self (Target), Delegate (Event) |
| `ClearDelegate` / `UnbindAllEvents` | `UK2Node_ClearDelegate` | same as AddDelegate but no Delegate pin. Pins: execute, then, self (Target) |
| `CreateDelegate` / `CreateEvent` | `UK2Node_CreateDelegate` | `{"function_name": "MyHandler"}` — bare name, NOT `ClassName.Function` format. Pins: self (Object), OutputDelegate (Event). Not a CustomEvent — creates a delegate object referencing a function |
| `Composite` | `UK2Node_Composite` | none — creates a collapsed composite subgraph. Read back `subgraph_name` from `list_nodes` output, then use it as `subgraph_path` to edit nodes inside the composite. |

**Removed short names** — no longer accepted: `FunctionEntry`, `FunctionResult`, `ForEachLoop`. For ForEach loops use `CallFunction` with `function_name: "KismetArrayLibrary.Array_ForEach"`.

**Unknown short names** return an explicit error listing all valid names — there is no silent fallback to `StaticLoadClass`.

**UK2Node_Event parameter format:** `"function_name"` must be `"ClassName.FunctionName"`. The class must exist in the engine and the function must be defined on it. Invalid class or function name returns `InvalidField` error.

**Sequence node outputs:** `"then 0"`, `"then 1"` etc. (space before number, not underscore).

**Example: Hello World Blueprint**
```python
# 1. Create Actor Blueprint
blueprint_cmd(command="create", params={"name": "BP_HelloWorld", "path": "/Game/Blueprints", "type": "Actor"})

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
blueprint_cmd(command="compile", params={"asset_path": "/Game/Blueprints/BP_HelloWorld"})
blueprint_cmd(command="save", params={"asset_path": "/Game/Blueprints/BP_HelloWorld"})
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
blueprint_compose (with Timeline node) -> blueprint_cmd(command="configure_timeline", params={...}) -> blueprint_cmd(command="compile")
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
blueprint_cmd(command="create", params={...}) → blueprint_cmd(command="add_scs_component", params={...}) → blueprint_cmd(command="set_component_defaults", params={...})
```

**Example: Create an owned StaticMeshComponent, then set mesh, material, transform, and visibility**
```python
create_result = blueprint_cmd(command="create", params={
    "name": "BP_Barrel",
    "path": "/Game/Blueprints",
    "type": "Actor"
})

component_result = blueprint_cmd(command="add_scs_component", params={
    "asset_path": "/Game/Blueprints/BP_Barrel",
    "component_class": "StaticMeshComponent",
    "component_name": "OwnedStaticMesh",
    "parent_component": "DefaultSceneRoot",
    "compile": False
})

owned_component_name = component_result["variable_name"]

defaults_result = blueprint_cmd(command="set_component_defaults", params={
    "asset_path": "/Game/Blueprints/BP_Barrel",
    "component_name": owned_component_name,
    "properties": {
        "StaticMesh": "/Game/Meshes/SM_Barrel.SM_Barrel",
        "OverrideMaterials[0]": "/Game/Materials/MI_Barrel_Rusty.MI_Barrel_Rusty",
        "RelativeLocation": {"X": 100, "Y": 0, "Z": 50},
        "RelativeRotation": {"Pitch": 0, "Yaw": 90, "Roll": 0},
        "bVisible": False
    },
    "compile": True,
    "save": False
})
```

`set_component_defaults` only mutates owned SCS component templates, such as components created
with `add_scs_component`. It does not mutate inherited or native parent components. Inspect
`partial_failure` and `errors[]` even when the command succeeds. Relative Blueprint paths default
to `/Game`; absolute mounted paths are valid when the root is project-owned and writable.

**Array property syntax:** `PropertyName[N]` is supported for indexed object-reference array slots
such as `OverrideMaterials[0]`; it is not generic arbitrary-array editing.

### Add an SCS Component

Use `blueprint_cmd(command="add_scs_component")` to add a component to a Blueprint's Components panel (SCS).

```python
# Add a StaticMeshComponent as a child of DefaultSceneRoot
blueprint_cmd(command="add_scs_component", params={
    "asset_path": "/Game/Blueprints/BP_JumpPad",
    "component_class": "StaticMeshComponent",
    "component_name": "JumpPadMesh",
    "parent_component": "DefaultSceneRoot",
    "compile": True
})
# Returns: {"variable_name": "JumpPadMesh", "component_class": "StaticMeshComponent", "is_scene_component": true, ...}
```

**Important:** Always use the returned `variable_name` for subsequent calls — the engine may deduplicate names. Only SceneComponent subclasses can specify `parent_component`.

**Typical workflow:** `add_scs_component` → `set_component_defaults` (set object-reference properties like StaticMesh asset).

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
  -> blueprint_cmd(command="remove_scs_component") (for each component now declared in C++ constructor)
  -> blueprint_cmd(command="compile")
```

### Add / Remove Interface

```python
# Add a Blueprint interface
blueprint_cmd(command="add_interface", params={
    "asset_path": "/Game/Blueprints/BP_Door",
    "interface_path": "/Game/Interfaces/BPI_Interactable",
    "compile": True
})
# Returns: {"interface_name": "BPI_Interactable_C", "stub_functions": ["ExecuteInteraction", "CanInteract"], ...}

# Add a C++ interface (short name)
blueprint_cmd(command="add_interface", params={
    "asset_path": "/Game/Blueprints/BP_Door",
    "interface_path": "BlendableInterface",
    "compile": True
})

# Remove an interface
blueprint_cmd(command="remove_interface", params={
    "asset_path": "/Game/Blueprints/BP_Door",
    "interface_path": "/Game/Interfaces/BPI_Interactable",
    "compile": True
})
# Returns: {"interface_name": "BPI_Interactable_C", "removed_graphs": ["ExecuteInteraction", "CanInteract"], ...}
```

**Interface path formats:** Blueprint asset path (`/Game/Interfaces/BPI_X`), C++ short name (`BlendableInterface`), or I-prefixed (`IBlendableInterface`).

**Validation:**
- Adding an already-implemented interface → `InvalidOperation`
- Removing a non-implemented interface → `InvalidOperation`
- Non-interface class → `InvalidOperation`
- Unresolvable class → `ClassNotFound`

### Configure Tick Settings
```
blueprint_cmd(set_tick_settings, asset_path, start_with_tick_enabled, tick_interval) → auto-compiles
```

**Example: Enable tick on an Actor Blueprint**
```python
blueprint_cmd(command="set_tick_settings", params={
    "asset_path": "/Game/Blueprints/BP_Enemy",
    "start_with_tick_enabled": True,
    "tick_interval": 0.1,
    "compile": True,
    "save": False
})
# Returns: {"can_ever_tick": true, "start_with_tick_enabled": true, "tick_interval": 0.1, "compiled": true, "saved": false}
```

**Smart auto-set:** Setting `start_with_tick_enabled: true` automatically forces `can_ever_tick: true`. Only Actor-based Blueprints support tick settings.

### Configure Replication Settings
```
blueprint_cmd(set_replication_settings, asset_path, replicates, net_dormancy, ...) → auto-compiles
```

**Example: Enable replication on an Actor Blueprint**
```python
blueprint_cmd(command="set_replication_settings", params={
    "asset_path": "/Game/Blueprints/BP_NetworkedActor",
    "replicates": True,
    "replicate_movement": True,
    "net_dormancy": "DORM_Awake",
    "compile": True,
    "save": False
})
# Returns: {"replicates": true, "replicate_movement": true, "net_dormancy": "DORM_Awake", "net_use_owner_relevancy": false, ...}
```

**Valid `net_dormancy` values:** `DORM_Never`, `DORM_Awake`, `DORM_DormantAll`, `DORM_DormantPartial`, `DORM_Initial`. Invalid values return `InvalidValue` with the valid list.

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

### Navigate Composite Subgraphs

Composite subgraphs (`UK2Node_Composite`) are collapsed regions inside a Blueprint graph. All graph tools accept an optional `subgraph_path` parameter to target nodes inside composites.

**Discover composites in a Blueprint:**
```python
# Method A: include_subgraphs on list_graphs
blueprint_cmd(command="graph_list_graphs", params={
    "asset_path": "/Game/Blueprints/BP_Actor",
    "include_subgraphs": True
})
# Returns top-level graphs plus composite entries with:
#   "kind": "ubergraph" | "function" | "macro" | "delegate" | "interface_impl"
#   "owning_interface": "InterfaceClassName"  # interface_impl only
#   "parent_graph": "EventGraph"
#   "subgraph_path": "MyComposite"

# Method B: read subgraph_name from list_nodes
blueprint_cmd(command="graph_get_subgraph", params={
    "asset_path": "/Game/Blueprints/BP_Actor",
    "graph_name": "EventGraph"
})
# Composite nodes include: "subgraph_name": "MyComposite"
# Tunnel boundary nodes include: "is_tunnel_boundary": true
```

Graph targeting is currently name-based. If names collide across graph kinds, graph
commands resolve the first match. Prefer unique graph names until graph commands
support a stable graph reference or graph-kind discriminator.

**Read nodes inside a composite:**
```python
blueprint_cmd(command="graph_get_subgraph", params={
    "asset_path": "/Game/Blueprints/BP_Actor",
    "graph_name": "EventGraph",
    "subgraph_path": "MyComposite"
})
```

**Add a node inside a composite:**
```python
blueprint_cmd(command="graph_add_node", params={
    "asset_path": "/Game/Blueprints/BP_Actor",
    "node_class": "CallFunction",
    "params": {"function_name": "KismetSystemLibrary.PrintString"},
    "graph_name": "EventGraph",
    "subgraph_path": "MyComposite"
})
```

**Connect nodes inside a composite:**
```python
blueprint_cmd(command="graph_connect", params={
    "asset_path": "/Game/Blueprints/BP_Actor",
    "source_node": "<tunnel_entry_id>",
    "source_pin": "then",
    "target_node": "<print_node_id>",
    "target_pin": "execute",
    "graph_name": "EventGraph",
    "subgraph_path": "MyComposite"
})
```

**Nested composites** — append path segments with dots (max 5 levels):
```python
blueprint_cmd(command="graph_get_subgraph", params={
    "asset_path": "/Game/Blueprints/BP_Actor",
    "graph_name": "EventGraph",
    "subgraph_path": "OuterComposite.InnerComposite"
})
```

**Search recursively across composites (default behavior):**
```python
blueprint_cmd(command="graph_search_nodes", params={
    "asset_path": "/Game/Blueprints/BP_Actor",
    "function_name": "PrintString"
})
# Results inside composites include "subgraph_path": "MyComposite"
```

**Use `blueprint_compose` to add nodes inside a composite:**
```python
# Step 1: create the Blueprint and add the Composite node to EventGraph
blueprint_compose(
    name="BP_CompositeActor", path="/Game/Blueprints/",
    nodes=[
        {"name": "BeginPlay", "class": "Event", "params": {"function_name": "Actor.ReceiveBeginPlay"}},
        {"name": "MyComposite", "class": "Composite"},
    ],
    connections=[{"from": "BeginPlay.then", "to": "MyComposite.execute"}]
)

# Step 2: read back subgraph_name from list_nodes, then add nodes inside it
blueprint_compose(
    mode="update",
    asset_path="/Game/Blueprints/BP_CompositeActor",
    graph_name="EventGraph",
    subgraph_path="<subgraph_name_from_list_nodes>",
    nodes=[
        {"name": "PrintMsg", "class": "CallFunction",
         "params": {"function_name": "KismetSystemLibrary.PrintString"},
         "pin_values": {"InString": "Inside composite!"}},
    ],
    connections=[{"from": "<tunnel_entry_id>.then", "to": "PrintMsg.execute"}]
)
```

**Safety rules:**
- Tunnel boundary nodes (`is_tunnel_boundary: true`) are structural — never delete or rewire them
- Composite names must not contain dots (the path separator)
- `subgraph_path` cannot be used with `blueprint_compose(mode="create")`
- Each `blueprint_compose` call targets a single subgraph level

**Error codes:**
- `SUBGRAPH_NOT_FOUND` — no composite with that name found in the graph
- `SUBGRAPH_DEPTH_EXCEEDED` — path exceeds the 5-level depth limit

### Review Blueprint
```
blueprint_cmd(get_blueprint_info) → blueprint_cmd(graph_list_graphs) → blueprint_cmd(graph_get_subgraph) per graph → assess complexity
```

**`get_blueprint_info` limitation:** The `functions` array only includes functions *defined on the Blueprint itself*. Inherited C++ functions (e.g. from a custom C++ base class) are **not listed**. To discover inherited C++ functions, use `query_class_detail(class_name, detail="full")` from the Reflect domain instead.

### Compact Serialization — Default Behavior of Graph Reads

`graph_get_subgraph`, `graph_get_subgraph`, `graph_search_nodes`, and `bp.get_info` accept an optional `compact` boolean parameter, **default `true`**. Compact mode trims fields that AI agents rarely need, reducing response size by ~25-35% on a typical 30-node EventGraph.

**What gets stripped with `compact=true`:**

| Command | Stripped fields |
|---------|-----------------|
| `graph_get_subgraph` | `position` object (x/y), `node_class` (duplicate of `class`), `pin_count` |
| `graph_get_subgraph` | `position`, `node_class`, hidden pins with no connections/defaults; surviving pins drop `is_connected: false` and empty `default_value` |
| `graph_search_nodes` | `node_class` (search results never included positions) |
| `bp.get_info` | empty `inputs` / `outputs` arrays on functions, `source` field on functions |

**Pin skip predicate** (applies only to `graph_get_subgraph`): a pin is excluded when ALL of these hold — `bHidden`, no `LinkedTo` connections, empty `DefaultValue`, empty `DefaultTextValue`, `DefaultObject == nullptr`. This preserves meaningful hidden class-reference pins (e.g. a hidden `WorldContextObject` pin with a non-null default).

**Preserved in every mode:** node `id`/`name`, node `class`, `display_name`, `connections`, pin `name`/`direction`/`type`. Compact mode never strips information needed to understand graph semantics — only noise.

**Examples:**
```python
# Default (compact=true) — use this for most reads
blueprint_cmd(command="graph_get_subgraph", params={
    "asset_path": "/Game/Blueprints/BP_Door",
    "graph_name": "EventGraph"
})

# Verbose (compact=false) — when you need positions or hidden pins
blueprint_cmd(command="graph_get_subgraph", params={
    "asset_path": "/Game/Blueprints/BP_Door",
    "graph_name": "EventGraph",
    "compact": False
})

blueprint_cmd(command="graph_get_subgraph", params={
    "asset_path": "/Game/Blueprints/BP_Door",
    "node_id": "K2Node_CallFunction_3",
    "compact": False  # include hidden pins for full inspection
})
```

**When to prefer `compact: false`:**
- **BP→C++ migration Ground Truth Table** — need every pin (including hidden class references) to produce faithful C++
- **Auto-layout verification** — need `position` x/y to check node placement after layout
- **Functions inventory audit** — need `source` field to distinguish `"blueprint"` from `"inherited"` functions in `bp.get_info`
- **Test assertions** — when a test explicitly checks for stripped fields

**When `compact: true` (default) is correct:**
- Tracing execution flow (connections are preserved)
- Finding entry points with `search_nodes`
- Counting nodes in a graph (total count is returned at top level, unaffected by compact)
- Reading variable defaults and types via `bp.get_info` (variables are not affected — only functions)

### Modify Existing Blueprint
```
blueprint_cmd(command="get_info") -> blueprint_cmd(command="add_variable"/"remove_variable"/"add_function") -> blueprint_cmd(command="compile") -> blueprint_cmd(command="save")
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

