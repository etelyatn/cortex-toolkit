# Material Patterns

Common material setups, instance hierarchies, and MCP tool workflows.

## Common Material Graphs

### PBR Opaque (Standard)
```
Nodes:
├── TextureSampleParameter2D "BaseColor" → BaseColor
├── TextureSampleParameter2D "Normal" → Normal
├── TextureSampleParameter2D "ORM" → split channels
│   ├── R (AO) → AmbientOcclusion
│   ├── G (Roughness) → Roughness
│   └── B (Metallic) → Metallic
└── VectorParameter "TintColor" → Multiply with BaseColor
```

### Masked (Foliage, Decals)
```
Nodes:
├── [PBR base nodes]
├── TextureSampleParameter2D "OpacityMask" → OpacityMask
├── ScalarParameter "MaskClip" (default: 0.333) → OpacityMask threshold
└── TwoSidedSign → for foliage backface normals
Blend Mode: Masked
```

### Emissive (Screens, Lights, Effects)
```
Nodes:
├── [PBR base nodes]
├── VectorParameter "EmissiveColor" (default: [1,1,1,1])
├── ScalarParameter "EmissiveIntensity" (default: 1.0)
└── Multiply (EmissiveColor * EmissiveIntensity) → EmissiveColor
```

### Transparent (Glass, Water, UI)
```
Nodes:
├── [PBR base nodes]
├── ScalarParameter "Opacity" (default: 0.5) → Opacity
├── Fresnel → Lerp alpha for edge opacity
└── ScalarParameter "Refraction" (default: 1.0) → Refraction
Blend Mode: Translucent
```

### Tiling / UV Control
```
Nodes:
├── TextureCoordinate
├── ScalarParameter "TilingU" (default: 1.0)
├── ScalarParameter "TilingV" (default: 1.0)
├── Append (TilingU, TilingV)
└── Multiply (TexCoord * Tiling) → UV input for texture samples
```

## Instance Hierarchy Patterns

### Layered Hierarchy
```
M_Master_PBR (base — all parameters exposed)
├── MI_Metal_Base (Metallic=1.0, Roughness=0.3)
│   ├── MI_Metal_Steel (BaseColor=steel tex, Normal=brushed)
│   ├── MI_Metal_Gold (BaseColor=gold tex, TintColor=warm)
│   └── MI_Metal_Copper (BaseColor=copper tex, Roughness=0.4)
├── MI_Wood_Base (Metallic=0.0, Roughness=0.7)
│   ├── MI_Wood_Oak (BaseColor=oak tex, Normal=wood grain)
│   └── MI_Wood_Pine (BaseColor=pine tex)
└── MI_Stone_Base (Metallic=0.0, Roughness=0.85)
    └── MI_Stone_Marble (BaseColor=marble tex, Normal=polished)
```

### Flat Hierarchy (Simple Projects)
```
M_Prop (base with standard PBR params)
├── MI_Prop_Chair
├── MI_Prop_Table
└── MI_Prop_Lamp
```

## Parameter Collection Patterns

### Environment Collection (MPC_Environment)
```
Scalars:
├── TimeOfDay (0.0–24.0) — drives sky, lighting, fog
├── WindStrength (0.0–1.0) — foliage animation intensity
├── WetnessFactor (0.0–1.0) — puddles, darkened surfaces
└── SnowAmount (0.0–1.0) — snow coverage blend

Vectors:
├── SunColor — directional light tint
├── SkyColor — ambient sky contribution
└── FogColor — distance fog tint
```

### Character Collection (MPC_Character)
```
Scalars:
├── DamageFlash (0.0–1.0) — hit feedback intensity
└── StealthOpacity (0.0–1.0) — invisibility effect

Vectors:
├── TeamColor — team-specific tint
└── OutlineColor — selection highlight
```

## MCP Tool Workflows

### Composite Tool Creation Pattern (Primary Method)

The `material_compose` composite tool is the **recommended** way to build materials. It leverages UnrealCortex's batch pipeline for atomic, reliable creation.

#### Why Use Composite Tools

**OLD approach (unreliable, slow):**
- 60+ individual MCP tool calls for a complex material
- Each call is a TCP round-trip (5+ minutes total)
- Fragile: failure at step 45 leaves orphaned partial asset
- Hard to recover: must delete partial asset manually
- 90% failure rate on large graphs

**NEW approach (atomic, fast):**
- Single `material_compose` call
- Atomic batch execution with stop-on-error
- Auto-cleanup on failure (deletes partial .uasset)
- <2 minutes, reliable
- Clear error reporting with recovery actions

#### Usage

```python
material_compose(
    name="M_PBR",
    path="/Game/Materials/",
    nodes=[
        {"name": "BaseColor", "class": "TextureSampleParameter2D", "params": {"Texture": "/Game/Textures/T_Base"}},
        {"name": "Normal", "class": "TextureSampleParameter2D", "params": {"Texture": "/Game/Textures/T_Normal"}},
        {"name": "ORM", "class": "TextureSampleParameter2D", "params": {"Texture": "/Game/Textures/T_ORM"}},
        {"name": "TintColor", "class": "VectorParameter", "params": {"ParameterName": "TintColor", "DefaultValue": [1,1,1,1]}},
        {"name": "Multiply", "class": "Multiply"}
    ],
    connections=[
        {"from": "BaseColor.RGB", "to": "Multiply.A"},
        {"from": "TintColor.0", "to": "Multiply.B"},
        {"from": "Multiply.0", "to": "Material.BaseColor"},
        {"from": "Normal.RGB", "to": "Material.Normal"},
        {"from": "ORM.R", "to": "Material.AmbientOcclusion"},
        {"from": "ORM.G", "to": "Material.Roughness"},
        {"from": "ORM.B", "to": "Material.Metallic"}
    ]
)
```

**Success response:**
```json
{
  "success": true,
  "asset_path": "/Game/Materials/M_PBR",
  "total_steps": 15,
  "node_count": 5,
  "connection_count": 7,
  "properties_set": 4,
  "total_timing_ms": 850,
  "steps_summary": {"create": 1, "add_node": 5, "set_node_property": 4, "connect": 7, "auto_layout": 1}
}
```

**Failure response (with auto-cleanup):**
```json
{
  "success": false,
  "summary": "Step 8 of 15 failed: material.connect - Output pin 'XYZ' not found on node",
  "asset_path": "/Game/Materials/M_PBR",
  "completed_steps": 8,
  "failed_step": {"index": 8, "command": "material.connect", "error": "Pin not found"},
  "total_steps": 15,
  "recovery_action": {"action": "deleted_partial", "path": "/Game/Materials/M_PBR"}
}
```

#### What Happens Under the Hood

1. **Validation** (Python MCP layer):
   - Required fields (name, path)
   - Node name uniqueness
   - Connection validity (source/target nodes exist, pin names known)
   - No user params starting with `$steps[` (prevents $ref collision)

2. **Translation** (Python):
   - Short class names → full UE names (`TextureSample` → `MaterialExpressionTextureSample`)
   - Generate batch commands: create → add nodes → set properties → connect
   - Wire `$ref` between steps: `$steps[0].data.asset_path`, `$steps[1].data.node_id`

3. **Batch Execution** (C++ CortexCore):
   - Deep-copy params before $ref resolution (preserve original request)
   - Resolve refs from previous step results
   - Execute sequentially on Game Thread
   - Defer PostEditChange/RebuildGraph until batch end (prevents freeze)
   - Single FScopedTransaction (one undo entry)
   - Halt on first failure (stop-on-error mode)

4. **Post-Batch** (Python):
   - Call `material.auto_layout` separately (non-critical, warns if fails)
   - On failure: delete partial asset, return recovery_action

#### $ref Wiring Patterns

The composite tool auto-generates $ref strings between steps:

**Pattern 1: Asset path propagation**
```json
// Step 0: create_material → returns {asset_path: "/Game/Materials/M_Test"}
// Step 1: add_node uses "$steps[0].data.asset_path"
// After resolution: asset_path = "/Game/Materials/M_Test"
```

**Pattern 2: Node ID chaining**
```json
// Step 1: add_node → returns {node_id: "MaterialExpressionConstant_0"}
// Step 5: connect uses "$steps[1].data.node_id" for source_node
// After resolution: source_node = "MaterialExpressionConstant_0"
```

**Pattern 3: Multi-step connection**
```json
// Connect two previously created nodes:
{
  "asset_path": "$steps[0].data.asset_path",    // Ref to create_material
  "source_node": "$steps[2].data.node_id",      // Ref to second add_node
  "target_node": "$steps[3].data.node_id"       // Ref to third add_node
}
```

**Type preservation:** $ref maintains JSON types (numbers stay numbers, not strings).

#### Failure Recovery

**Auto-cleanup on failure:**
If batch fails mid-execution and step 0 (create_material) succeeded, the composite tool automatically deletes the partial asset:

```python
if failed_step is not None and asset_path:
    connection.send_command("material.delete_material", {"asset_path": asset_path})
    return {
        "success": False,
        "recovery_action": {"action": "deleted_partial", "path": asset_path}
    }
```

This prevents `ASSET_ALREADY_EXISTS` errors on retry.

**Recovery actions:**
- `deleted_partial`: Partial asset was deleted, safe to retry
- `cleanup_failed`: Deletion failed, manual intervention required (path provided)

#### Timeout Scaling

Composite tools scale TCP timeout dynamically to handle large graphs:
```python
timeout = max(60, len(commands) * 2)  # 60s minimum, 2s per command
```

A 127-step batch gets 254s timeout instead of the default 60s.

### Manual Batch Construction (Advanced)

For updating existing materials or edge cases not covered by composite tools, construct batches manually.

#### When to Use Manual Batches

- Modifying existing materials (add/remove nodes, rewire connections)
- Complex updates requiring atomicity but not full graph recreation
- Operations not yet supported by composite tools

#### Example: Add Parameter to Existing Material

```json
{
  "command": "batch",
  "params": {
    "stop_on_error": true,
    "commands": [
      {"command": "material.add_node", "params": {
        "asset_path": "/Game/Materials/M_Existing",
        "expression_class": "MaterialExpressionScalarParameter"
      }},
      {"command": "material.set_node_property", "params": {
        "asset_path": "/Game/Materials/M_Existing",
        "node_id": "$steps[0].data.node_id",
        "property_name": "ParameterName",
        "value": "Metallic"
      }},
      {"command": "material.set_node_property", "params": {
        "asset_path": "/Game/Materials/M_Existing",
        "node_id": "$steps[0].data.node_id",
        "property_name": "DefaultValue",
        "value": 0.5
      }},
      {"command": "material.connect", "params": {
        "asset_path": "/Game/Materials/M_Existing",
        "source_node": "$steps[0].data.node_id",
        "source_output": "0",
        "target_node": "MaterialResult",
        "target_input": "Metallic"
      }},
      {"command": "material.auto_layout", "params": {
        "asset_path": "/Game/Materials/M_Existing"
      }}
    ]
  }
}
```

**Key differences from composite tools:**
- Direct asset path (not a new material, so no create step)
- Manual $ref wiring (Python layer doesn't auto-generate)
- No spec validation (you're responsible for correctness)
- No auto-cleanup on failure (partial changes remain)

#### $ref Syntax Reference

**Basic field reference:**
```
$steps[0].data.asset_path
$steps[1].data.node_id
```

**Nested field reference:**
```
$steps[0].data.created.id
$steps[2].data.connections[0].pin
```

**Escape literal strings:**
```
"$$steps[0]"  →  resolves to "$steps[0]" (literal)
```

**Rules:**
- Must be entire string value (no mid-string interpolation)
- Only references to previous steps (N < current step index)
- References to failed steps return error
- Type-preserving (numbers stay numbers, bools stay bools)

#### Error Handling in Manual Batches

**stop_on_error: true (recommended for atomic operations):**
Halts at first failure, returns all completed steps + error:
```json
{
  "success": true,
  "data": {
    "results": [
      {"index": 0, "success": true, "data": {...}, "timing_ms": 10.2},
      {"index": 1, "success": false, "error_code": "INVALID_FIELD", "error_message": "...", "timing_ms": 1.3}
    ],
    "count": 2,
    "total_timing_ms": 11.5
  }
}
```

**stop_on_error: false (default, for independent operations):**
Executes all steps regardless of failures:
```json
{
  "success": true,
  "data": {
    "results": [
      {"index": 0, "success": true, ...},
      {"index": 1, "success": false, "error_code": "ASSET_NOT_FOUND", ...},
      {"index": 2, "success": true, ...}
    ],
    "count": 3
  }
}
```

**$ref resolution errors:**
- Future/self reference: `BATCH_REF_RESOLUTION_FAILED: Ref to step N out of bounds`
- Failed step: `BATCH_REF_RESOLUTION_FAILED: Ref to failed step N`
- Missing field: `BATCH_REF_RESOLUTION_FAILED: Field 'X' not found in step N data`
- Malformed: `BATCH_REF_RESOLUTION_FAILED: Malformed ref`

#### Performance Characteristics

| Batch Size | Typical Duration | Notes |
|------------|------------------|-------|
| 10 commands | 50-100ms | Small graph modifications |
| 50 commands | 200-400ms | Medium material graph |
| 127 commands | 800-1500ms | Production material (40 nodes) |
| 200 commands | 1000-2000ms | Max batch size |

**Optimization:** Batch-aware operations defer `PostEditChange`/`RebuildGraph` until batch end, preventing 5-30s editor freeze on large batches.

### Set Material-Level Properties
```
get_material (asset_path) → check current settings
→ set_material_property (asset_path, property_name, value) ×N
```

**Example: Configure Post-Process Material**
```python
# Set domain, blend mode, and shading model
set_material_property("/Game/Materials/M_Outline", "MaterialDomain", "PostProcess")
set_material_property("/Game/Materials/M_Outline", "ShadingModel", "Unlit")
set_material_property("/Game/Materials/M_Outline", "BlendMode", "Translucent")
```

**Example: Make Foliage Material Two-Sided and Masked**
```python
set_material_property("/Game/Materials/M_Leaves", "TwoSided", true)
set_material_property("/Game/Materials/M_Leaves", "BlendMode", "Masked")
```

**Enum aliases:** Use pretty names (`"Opaque"`, `"PostProcess"`, `"Unlit"`) or UE reflection names (`"BLEND_Opaque"`, `"MD_PostProcess"`, `"MSM_Unlit"`). The Python layer normalizes automatically.

### Set Expression Node Enum Properties
```
set_material_node_property (asset_path, node_id, property_name, value)
```

Now supports FByteProperty and FEnumProperty (SceneTextureId, SamplerType, etc.):

```python
# Configure SceneTexture for post-process input
set_material_node_property("/Game/Materials/M_PP", "Expr_0", "SceneTextureId", "PPI_PostProcessInput0")

# Set sampler type
set_material_node_property("/Game/Materials/M_Mat", "Expr_1", "SamplerType", "SAMPLERTYPE_Color")
```

### Individual Tool Usage (Legacy, Not Recommended)

⚠️ Only use individual tools when modifying existing materials and a batch is unnecessary.
   For new materials, always use `material_compose` composite tool.
   For complex updates, use manual batch construction.

```
add_node (asset_path, expression_class)
→ set_node_property (asset_path, node_id, property_name, value)
→ connect_material_nodes (asset_path, source_node, source_output, target_node, target_input)
→ auto_layout (asset_path)
```

### Create Instance with Overrides
```
create_instance (asset_path, name, parent_material)
→ set_parameters ([
    {name: "BaseColor", value: "/Game/Textures/T_Brick_D"},
    {name: "Normal", value: "/Game/Textures/T_Brick_N"},
    {name: "TintColor", value: [0.9, 0.85, 0.8, 1.0]},
    {name: "Roughness", value: 0.85}
  ])
```

### Modify Instance Parameters
```
list_parameters (instance path) → see current values
→ set_parameter (name, new value) or set_parameters (batch)
→ get_instance (verify overrides)
```

### Reset Instance to Parent Defaults
```
list_parameters (instance path) → identify overridden params
→ reset_parameter (name) for each override to clear
→ get_instance (verify clean state)
```

### Set Up Parameter Collection
```
create_collection (asset_path, name)
→ add_collection_parameter (name: "TimeOfDay", type: "scalar", default: 12.0)
→ add_collection_parameter (name: "SunColor", type: "vector", default: [1,0.95,0.8,1])
→ set_collection_parameter (name, value) to adjust at runtime
```

### Audit Material Graph
```
list_materials (path, recursive) → find all materials
→ get_material (each) → check node count, connections
→ list_nodes (each) → identify unused nodes
→ list_connections (each) → verify all outputs are connected (includes expression-to-expression)
→ get_material_node_pins (each node) → verify pin usage
```

### Delete Materials and Instances (Improved: Actual File Deletion)
```
delete_material (asset_path)
→ Uses ObjectTools::ForceDeleteObjects for proper reference cleanup
→ Deletes .uasset file from disk (not just MarkAsGarbage)
→ Returns error if material has references that prevent deletion
→ Returns {asset_path, deleted: true} on success

delete_instance (asset_path)
→ Same disk deletion behavior as delete_material
→ Cleanup is reliable — no orphaned files after deletion
```

### Set Node Properties (Improved: Struct + Enum Property Support)
```
set_node_property (asset_path, node_id, property_name, value)
→ Supports FLinearColor properties (e.g., VectorParameter.DefaultValue)
→ Supports FVector properties
→ Supports FByteProperty / FEnumProperty (e.g., SceneTextureId, SamplerType)
→ Format for FLinearColor: [R, G, B, A] as array of floats
→ Format for Enum: UE enum string ("PPI_PostProcessInput0") or integer value
→ Example: set_node_property(..., "DefaultValue", [1.0, 0.0, 0.0, 1.0])
→ Example: set_node_property(..., "SceneTextureId", "PPI_PostProcessInput0")
→ Delegates to FCortexSerializer::JsonToProperty for all type resolution
```

## Pin Naming Reference

### Composite Tool Pin Validation
The `material_compose` composite tool validates pin names against a comprehensive _PIN_MAP covering 30+ expression types before executing the batch. This catches pin name errors early and prevents cascading failures.

Validated expression types include:
- Parameters: ScalarParameter, VectorParameter, TextureParameter, StaticSwitchParameter, StaticBoolParameter
- Constants: Constant, Constant2Vector, Constant3Vector, Constant4Vector
- Math binary: Multiply, Add, Subtract, Divide, Power, DotProduct, CrossProduct
- Math unary: OneMinus, Abs, Sine, Cosine, Floor, Ceil, Frac, Normalize
- Interpolation: Lerp, Clamp, If
- Texture: TextureCoordinate, TextureSample, TextureObject
- Animation: Time, Panner
- World: WorldPosition, VertexColor
- Vector ops: ComponentMask, AppendVector, Desaturation
- Special: Fresnel, Noise

### Output Pins (source_output in connections)
- **Most nodes**: `"0"` (single unnamed output)
- **Texture nodes** (TextureSample, TextureParameter): `"RGBA"`, `"RGB"`, `"R"`, `"G"`, `"B"`, `"A"`
- **VertexColor**: `"RGBA"`, `"RGB"`, `"R"`, `"G"`, `"B"`, `"A"`
- **ComponentMask**: `"0"` (output depends on configured channels)

### Input Pins (target_input in connections)
| Node Type | Input Pins |
|-----------|------------|
| Math binary (Multiply, Add, Subtract, Divide, DotProduct, CrossProduct) | `"A"`, `"B"` |
| Math unary (Sine, Cosine, Abs, OneMinus, Floor, Ceil, Frac) | `"Input"` |
| Normalize | `"VectorInput"` |
| Lerp/LinearInterpolate | `"A"`, `"B"`, `"Alpha"` |
| Clamp | `"Input"`, `"Min"`, `"Max"` |
| If | `"A"`, `"B"`, `"AGreaterThanB"`, `"AEqualsB"`, `"ALessThanB"` |
| Power | `"Base"`, `"Exp"` |
| TextureSample | `"UVs"`, `"Tex"` |
| Panner | `"Coordinate"`, `"Time"`, `"Speed"`, `"SpeedX"`, `"SpeedY"` |
| Fresnel | `"ExponentIn"`, `"BaseReflectFractionIn"`, `"Normal"` |
| ComponentMask | `"Input"` |
| AppendVector | `"A"`, `"B"` |
| Desaturation | `"Input"`, `"Fraction"` |
| Noise | `"Position"` |
| StaticSwitchParameter | `"True"`, `"False"`, `"Value"` |
| MaterialResult | `"BaseColor"`, `"Metallic"`, `"Roughness"`, `"Normal"`, `"EmissiveColor"`, `"Specular"`, `"Opacity"`, `"OpacityMask"`, `"WorldPositionOffset"`, `"AmbientOcclusion"` |

### Discovering Pins at Runtime (New: get_material_node_pins)
Use `get_material_node_pins(asset_path, node_id)` to query actual pin names on any node.
This is the definitive way to discover available pins and see what's currently connected.

```
get_material_node_pins("/Game/Materials/M_Test", "Expr_0")
→ Returns: {
    "node_id": "Expr_0",
    "expression_class": "MaterialExpressionMultiply",
    "outputs": [{index: 0, name: "0"}],
    "inputs": [
      {index: 0, name: "A", connected_to: "Expr_1"},
      {index: 1, name: "B"}
    ],
    "input_count": 2,
    "output_count": 1
  }

Use case:
1. Add a node with add_material_node
2. Get its node_id from the response
3. Call get_material_node_pins to discover exact pin names
4. Use discovered pin names in connect_material_nodes
```

## Benchmark Tests

Material domain workflows are validated by the benchmark testing framework in `Plugins/UnrealCortex/MCP/tests/`:

| Test File | Coverage |
|-----------|----------|
| `test_material_composites.py` | `material_compose` composite end-to-end, node/connection validation, failure recovery, auto-cleanup |
| `test_material_composites_e2e.py` | `set_material_property`, `set_material_node_property`, enum/byte property support |
| `test_material_enum_aliases.py` | Pretty name to UE reflection name mapping (MaterialDomain, BlendMode, ShadingModel) |
| `test_mcp_scenarios.py` | Material Create benchmark (create graph + create instance + set parameter) |

Run to validate after modifying Material MCP tools or C++ command handlers.
