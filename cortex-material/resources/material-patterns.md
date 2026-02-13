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

### Build a PBR Material from Scratch (Recommended: Composite Tool)
```
create_material_graph (name, path, nodes, connections)
→ Atomically creates material + all nodes + connections in single batch
→ Pre-validates node specs and pin names before execution
→ Auto-cleans partial assets on failure (deletes .uasset files)
→ Runs auto_layout after completion (warns if fails, non-critical)
→ Scales timeout dynamically for large graphs
→ Returns detailed failure info (completed_steps, failed_step, recovery_action)

Example nodes spec (with params):
[
  {name: "BaseColor", class: "TextureSampleParameter2D", params: {Texture: "/Game/Textures/T_Base"}},
  {name: "Normal", class: "TextureSampleParameter2D", params: {Texture: "/Game/Textures/T_Normal"}},
  {name: "ORM", class: "TextureSampleParameter2D", params: {Texture: "/Game/Textures/T_ORM"}},
  {name: "TintColor", class: "VectorParameter", params: {ParameterName: "TintColor", DefaultValue: [1,1,1,1]}},
  {name: "Multiply", class: "Multiply"}
]

Example connections spec (use named pins):
[
  {from: "BaseColor.RGB", to: "Multiply.A"},
  {from: "TintColor.0", to: "Multiply.B"},
  {from: "Multiply.0", to: "Material.BaseColor"},
  {from: "Normal.RGB", to: "Material.Normal"},
  {from: "ORM.R", to: "Material.AmbientOcclusion"},
  {from: "ORM.G", to: "Material.Roughness"},
  {from: "ORM.B", to: "Material.Metallic"}
]

Success response:
{
  "success": true,
  "asset_path": "/Game/Materials/M_PBR",
  "total_steps": 15,
  "node_count": 5,
  "connection_count": 7,
  "properties_set": 4,
  "total_timing_ms": 850,
  "steps_summary": {create: 1, add_node: 5, set_node_property: 4, connect: 7, auto_layout: 1}
}

Failure response (with auto-cleanup):
{
  "success": false,
  "summary": "Step 8 of 15 failed: material.connect - Output pin 'XYZ' not found on node",
  "asset_path": "/Game/Materials/M_PBR",
  "completed_steps": 8,
  "failed_step": {index: 8, command: "material.connect", error: "Pin not found"},
  "total_steps": 15,
  "recovery_action": {action: "deleted_partial", path: "/Game/Materials/M_PBR"}
}
```

### Build a Material with Individual Tools (Modifying Existing Only)
```
⚠️ Only use individual tools when modifying existing materials.
   For new materials, always use create_material_graph composite tool.

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

### Set Node Properties (Improved: Struct Property Support)
```
set_node_property (asset_path, node_id, property_name, value)
→ Now supports FLinearColor properties (e.g., VectorParameter.DefaultValue)
→ Now supports FVector properties
→ Format for FLinearColor: [R, G, B, A] as array of floats
→ Example: set_node_property(..., "DefaultValue", [1.0, 0.0, 0.0, 1.0])
→ Previously only supported scalar/string properties
```

## Pin Naming Reference

### Composite Tool Pin Validation
The `create_material_graph` composite tool validates pin names against a comprehensive _PIN_MAP covering 30+ expression types before executing the batch. This catches pin name errors early and prevents cascading failures.

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
