# Material Graph Update Guide

Guide for AI agents updating existing material graphs using batches of low-level MCP commands. No composite tool needed — the agent reads current state, determines changes, and sends a single batch. Uses `$ref` syntax from the batch pipeline — see batch pipeline design doc for resolution rules.

## Pattern: validate → read → batch(mutate) → auto_layout

```
1. AI calls get_material                       ← validate material exists
2. AI calls list_nodes + list_connections       ← read current state (2 TCP calls)
3. AI validates the diff                        ← pre-flight checks (see below)
4. AI builds a batch of low-level commands      ← mix of literals + $ref for new nodes
5. auto_layout as final batch step              ← repositions everything cleanly
```

**Key difference from creation:** For updates, the AI already knows `asset_path` and existing `node_id` values as **literals** from the read step. Only newly added nodes need `$ref`.

## Pre-flight Validation (before sending batch)

The AI MUST validate before constructing the batch. These checks prevent wasted operations and partial state:

| Check | How | Failure action |
|-------|-----|----------------|
| Material exists | `get_material(asset_path)` | **Stop.** Ask user: wrong path? create new material instead? |
| Referenced nodes exist | Compare node_ids against `list_nodes` result | **Stop.** Show user which nodes are missing |
| Connections to disconnect exist | Compare against `list_connections` result | **Warn.** Skip the disconnect (connection may have been removed already) |
| Expression class valid | Check class name against known UE classes | **Stop.** Show user the invalid class name |
| Pin indices valid | Check against known pin counts for the expression class | **Stop.** Show user valid pin range |

If pre-flight fails, present the error to the user with options:

```
Cannot update material: /Game/Materials/M_PulsatingGradient

   Material not found at this path.

   Options:
   1. Check the correct path (list_materials to see available materials)
   2. Create a new material with create_material_graph
   3. Provide the correct asset path
```

```
Cannot update material: node "MaterialExpressionLinearInterpolate_0" not found

   The Gradient (Lerp) node referenced in the disconnect step does not exist
   in the current graph. Available Lerp nodes: MaterialExpressionLinearInterpolate_1

   Options:
   1. Use the correct node ID (MaterialExpressionLinearInterpolate_1)
   2. Skip this modification
   3. Re-read the graph to get fresh node IDs
```

## Command Ordering for Safe Updates

The batch command order matters for updates. Place operations in **dependency-safe order**:

```
1. add_node        ← new nodes first (no side effects if batch fails here)
2. set_node_property ← configure new nodes (still no graph impact)
3. disconnect      ← break old connections (graph changes start here — DANGER ZONE)
4. connect         ← wire new connections (must follow disconnect)
5. auto_layout     ← cosmetic, always last
```

**Why this order:** If the batch fails during `add_node` or `set_node_property` (steps 1-2), the existing graph is untouched — just orphan nodes were added. The risky part is `disconnect` → `connect` (steps 3-4), because a failure between them leaves the graph partially rewired.

## Example: Add circular mask to existing pulsating gradient

```json
{"command": "batch", "params": {"stop_on_error": true, "commands": [
  {"command": "material.add_node",          "params": {"asset_path": "/Game/Materials/M_PulsatingGradient", "expression_class": "MaterialExpressionSphereMask"}},
  {"command": "material.add_node",          "params": {"asset_path": "...", "expression_class": "MaterialExpressionMultiply"}},
  {"command": "material.set_node_property", "params": {"asset_path": "...", "node_id": "$steps[0].data.node_id", "property": "AttenuationRadius", "value": 0.5}},
  {"command": "material.disconnect",        "params": {"asset_path": "...", "source_node": "MaterialExpressionLinearInterpolate_0", "target_node": "MaterialResult", "target_input": "BaseColor"}},
  {"command": "material.connect",           "params": {"asset_path": "...", "source_node": "MaterialExpressionLinearInterpolate_0", "target_node": "$steps[1].data.node_id", "target_input": 0}},
  {"command": "material.connect",           "params": {"asset_path": "...", "source_node": "$steps[0].data.node_id", "target_node": "$steps[1].data.node_id", "target_input": 1}},
  {"command": "material.connect",           "params": {"asset_path": "...", "source_node": "$steps[1].data.node_id", "target_node": "MaterialResult", "target_input": "BaseColor"}},
  {"command": "material.auto_layout",       "params": {"asset_path": "/Game/Materials/M_PulsatingGradient"}}
]}}
```

## $ref Usage in Updates

| Param | Source | Example |
|-------|--------|---------|
| `asset_path` | Literal (known) | `"/Game/Materials/M_PulsatingGradient"` |
| Existing `node_id` | Literal (from `list_nodes`) | `"MaterialExpressionLinearInterpolate_0"` |
| New `node_id` | `$ref` (from `add_node` in this batch) | `"$steps[0].data.node_id"` |
| `"MaterialResult"` | Literal (always) | `"MaterialResult"` |

## Update Error Recovery

Update errors are more dangerous than creation errors because the graph is in a **partially modified state**. Always inform the user when a disconnect+connect sequence fails partway through — the material is in a broken visual state until fixed.

**Failure scenarios and recovery:**

| Failed at | Graph state | Recovery options for user |
|-----------|-------------|--------------------------|
| `add_node` (step 0-1) | **Safe.** Existing graph untouched | Fix expression class and retry |
| `set_node_property` (step 2) | **Safe.** New nodes exist but unconnected, graph works | Fix property and retry, or remove orphan nodes |
| `disconnect` (step 3) | **Safe.** Connection doesn't exist (already removed?) | Skip disconnect and continue with connects |
| `connect` after `disconnect` (step 4-6) | **BROKEN.** BaseColor unwired | **Ask user:** fix connection and retry, OR re-wire original connection as rollback |
| `auto_layout` (step 7) | **Functional.** Graph works, just messy layout | Call `auto_layout` separately, or ignore |

**Example: connect fails after disconnect:**

```
Material update partially completed: /Game/Materials/M_PulsatingGradient

   Step 4 of 8 failed: Connect Gradient → NewMultiply.A
   Error: Input pin index 3 does not exist on MaterialExpressionMultiply_2

   BaseColor is currently UNWIRED (disconnect at step 3 succeeded)

   What would you like to do?
   1. Fix the pin index and retry remaining connections (steps 4-7)
   2. Rollback: re-wire original connection (Gradient → Material.BaseColor) and remove new nodes
   3. Open the material in UE Editor and fix manually
```

This is why `stop_on_error: true` is critical for updates — continuing after a failed disconnect+connect could leave the graph in an even worse state.

## Pattern: Set Material-Level Properties

Use `set_material_property` to configure material-level settings like domain, blend mode, shading model, and two-sided rendering. This is separate from expression node properties.

### Workflow

```
1. AI calls get_material                       ← read current settings
2. AI calls set_material_property (×N)         ← change material-level properties
```

### Enum Alias Map

The Python MCP layer normalizes pretty names to UE reflection names automatically:

| Property | Pretty Name | UE Reflection Name |
|----------|-------------|-------------------|
| `BlendMode` | `"Opaque"` | `"BLEND_Opaque"` |
| `BlendMode` | `"Masked"` | `"BLEND_Masked"` |
| `BlendMode` | `"Translucent"` | `"BLEND_Translucent"` |
| `BlendMode` | `"Additive"` | `"BLEND_Additive"` |
| `BlendMode` | `"Modulate"` | `"BLEND_Modulate"` |
| `MaterialDomain` | `"Surface"` | `"MD_Surface"` |
| `MaterialDomain` | `"DeferredDecal"` | `"MD_DeferredDecal"` |
| `MaterialDomain` | `"LightFunction"` | `"MD_LightFunction"` |
| `MaterialDomain` | `"PostProcess"` | `"MD_PostProcess"` |
| `MaterialDomain` | `"UI"` | `"MD_UI"` |
| `ShadingModel` | `"Unlit"` | `"MSM_Unlit"` |
| `ShadingModel` | `"DefaultLit"` | `"MSM_DefaultLit"` |
| `ShadingModel` | `"Subsurface"` | `"MSM_Subsurface"` |
| `ShadingModel` | `"ClearCoat"` | `"MSM_ClearCoat"` |

Both formats are accepted. Use pretty names for readability.

### Example: Convert Material to Post-Process

```python
# 1. Check current material state
get_material("/Game/Materials/M_Outline")

# 2. Change domain to PostProcess and shading to Unlit
set_material_property("/Game/Materials/M_Outline", "MaterialDomain", "PostProcess")
set_material_property("/Game/Materials/M_Outline", "ShadingModel", "Unlit")
set_material_property("/Game/Materials/M_Outline", "BlendMode", "Translucent")
```

### Example: Make Material Two-Sided for Foliage

```python
set_material_property("/Game/Materials/M_Leaves", "TwoSided", true)
set_material_property("/Game/Materials/M_Leaves", "BlendMode", "Masked")
```

### Combining with Graph Updates

Material property changes can be included in the same batch as graph modifications. Place `set_material_property` commands after `add_node` but before `connect`:

```json
{"command": "batch", "params": {"stop_on_error": true, "commands": [
  {"command": "material.set_material_property", "params": {"asset_path": "/Game/Materials/M_Glass", "property_name": "BlendMode", "value": "BLEND_Translucent"}},
  {"command": "material.set_material_property", "params": {"asset_path": "/Game/Materials/M_Glass", "property_name": "TwoSided", "value": true}},
  {"command": "material.add_node", "params": {"asset_path": "/Game/Materials/M_Glass", "expression_class": "MaterialExpressionScalarParameter"}},
  {"command": "material.set_node_property", "params": {"asset_path": "/Game/Materials/M_Glass", "node_id": "$steps[2].data.node_id", "property_name": "ParameterName", "value": "Opacity"}},
  {"command": "material.set_node_property", "params": {"asset_path": "/Game/Materials/M_Glass", "node_id": "$steps[2].data.node_id", "property_name": "DefaultValue", "value": 0.5}},
  {"command": "material.connect", "params": {"asset_path": "/Game/Materials/M_Glass", "source_node": "$steps[2].data.node_id", "source_output": "0", "target_node": "MaterialResult", "target_input": "Opacity"}},
  {"command": "material.auto_layout", "params": {"asset_path": "/Game/Materials/M_Glass"}}
]}}
```

## Pattern: Set Expression Node Enum Properties

The `set_material_node_property` tool (refactored) now supports FByteProperty and FEnumProperty via FCortexSerializer::JsonToProperty. This enables setting enum values like SceneTextureId and SamplerType on expression nodes.

### Example: Configure SceneTexture Node for Post-Process

```python
# Add a SceneTexture node and configure it for post-process input
add_material_node("/Game/Materials/M_PP", "MaterialExpressionSceneTexture")
# Set SceneTextureId to PostProcessInput0
set_material_node_property("/Game/Materials/M_PP", "Expr_0", "SceneTextureId", "PPI_PostProcessInput0")
```

### Example: Configure Texture Sampler Type

```python
set_material_node_property("/Game/Materials/M_Mat", "Expr_1", "SamplerType", "SAMPLERTYPE_Color")
```
