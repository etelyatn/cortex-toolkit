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
→ Auto-validates pin names before execution
→ Auto-cleans partial assets on failure
→ Runs auto_layout after completion

Example nodes spec:
[
  {name: "BaseColor", class: "TextureSampleParameter2D"},
  {name: "Normal", class: "TextureSampleParameter2D"},
  {name: "ORM", class: "TextureSampleParameter2D"},
  {name: "TintColor", class: "VectorParameter", params: {DefaultValue: [1,1,1,1]}},
  {name: "Multiply", class: "Multiply"}
]

Example connections spec:
[
  {from: "BaseColor.RGB", to: "Multiply.A"},
  {from: "TintColor.0", to: "Multiply.B"},
  {from: "Multiply.0", to: "Material.BaseColor"},
  {from: "Normal.RGB", to: "Material.Normal"},
  {from: "ORM.R", to: "Material.AmbientOcclusion"},
  {from: "ORM.G", to: "Material.Roughness"},
  {from: "ORM.B", to: "Material.Metallic"}
]
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
→ list_connections (each) → verify all outputs are connected
```

## Pin Naming Reference

### Output Pins (source_output in connections)
- **Most nodes**: `"0"` (single unnamed output)
- **Texture nodes**: `"RGBA"`, `"RGB"`, `"R"`, `"G"`, `"B"`, `"A"`
- **ComponentMask**: `"R"`, `"G"`, `"B"`, `"A"`, `"RG"`, `"RGB"`, etc.

### Input Pins (target_input in connections)
| Node Type | Input Pins |
|-----------|------------|
| Math binary (Multiply, Add, Subtract, Divide) | `"A"`, `"B"` |
| Math unary (Sine, Cosine, Abs, OneMinus, Floor, Ceil, Frac) | `"Input"` |
| Lerp/LinearInterpolate | `"A"`, `"B"`, `"Alpha"` |
| Clamp | `"Input"`, `"Min"`, `"Max"` |
| Power | `"Base"`, `"Exp"` |
| TextureSample | `"UVs"`, `"Tex"` |
| Panner | `"Coordinate"`, `"Time"`, `"Speed"` |
| MaterialResult | `"BaseColor"`, `"Metallic"`, `"Roughness"`, `"Normal"`, `"EmissiveColor"`, `"Specular"`, `"Opacity"`, `"OpacityMask"`, `"AmbientOcclusion"` |

### Discovering Pins at Runtime
Use `get_material_node_pins(asset_path, node_id)` to query actual pin names on any node:
```
get_material_node_pins("/Game/Materials/M_Test", "Expr_0")
→ Returns: {
    "outputs": [{index: 0, name: "0"}],
    "inputs": [{index: 0, name: "A", connected_to: "Expr_1"}, ...]
  }
```
