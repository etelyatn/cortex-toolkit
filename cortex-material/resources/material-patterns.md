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

### Build a PBR Material from Scratch
```
create_material (asset_path, name)
→ add_node (TextureSampleParameter2D, position for BaseColor)
→ add_node (TextureSampleParameter2D, position for Normal)
→ add_node (TextureSampleParameter2D, position for ORM)
→ add_node (VectorParameter, position for TintColor)
→ add_node (Multiply, position for tint blend)
→ connect (BaseColor tex → Multiply A)
→ connect (TintColor → Multiply B)
→ connect (Multiply → Material BaseColor)
→ connect (Normal tex → Material Normal)
→ connect (ORM tex channels → Material Roughness, Metallic, AO)
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
