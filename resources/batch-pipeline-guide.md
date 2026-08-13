# Batch Pipeline Guide

Comprehensive reference for UnrealCortex batch command with $ref resolution and stop-on-error.

## Overview

The `batch` built-in command executes multiple commands sequentially with optional cross-step data references (`$ref`) and error handling control. This enables atomic multi-step operations like creating a material with nodes and connections in a single round-trip.

## Basic Usage

```json
{
  "command": "batch",
  "params": {
    "stop_on_error": true,
    "commands": [
      {"command": "material.create_material", "params": {"name": "M_Test", "asset_path": "/Game/Materials/"}},
      {"command": "material.add_node", "params": {"asset_path": "$steps[0].data.asset_path", "expression_class": "MaterialExpressionConstant"}}
    ]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {"index": 0, "success": true, "data": {"asset_path": "/Game/Materials/M_Test"}, "timing_ms": 12.3},
      {"index": 1, "success": true, "data": {"node_id": "MaterialExpressionConstant_0"}, "timing_ms": 2.1}
    ],
    "count": 2,
    "total_timing_ms": 14.4
  }
}
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `commands` | array | required | Array of command objects with `command` and `params` fields |
| `steps` | array | optional | Alias for `commands` |
| `stop_on_error` | bool | `false` | Halt execution at first failure (recommended for atomic operations) |
| `rollback_on_error` | bool | `false` | Publish rollback metadata; actual graph rollback is editor-dependent |
| `verify_rollback` | bool | `false` | Publish rollback verification metadata; actual verification is editor-dependent |

For the MCP-facing `core.batch_query` router path, `rollback_on_error` and `verify_rollback` are forwarded transparently to the editor's `batch` command. They do not alter Python-level batch behavior on this branch.

**Limits:**
- MaxBatchSize: 200 commands per batch
- Max recursion depth: 10 levels for nested JSON resolution
- Max message size: 2MB

## $ref Resolution

String parameter values matching `$steps[N].data.field` are resolved from previous step results before execution.

### Syntax

```
$steps[INDEX].data.path.to.field
```

- Must be the **entire string value** (no mid-string interpolation)
- Works in nested objects and arrays
- Preserves JSON types (numbers stay numbers, bools stay bools)

### Example: Material Creation

```json
{
  "commands": [
    {"command": "material.create_material", "params": {"name": "M_Test", "asset_path": "/Game/Materials/"}},
    {"command": "material.add_node", "params": {
      "asset_path": "$steps[0].data.asset_path",
      "expression_class": "MaterialExpressionConstant"
    }},
    {"command": "material.connect", "params": {
      "asset_path": "$steps[0].data.asset_path",
      "source_node": "$steps[1].data.node_id",
      "source_output": "0",
      "target_node": "MaterialResult",
      "target_input": "BaseColor"
    }}
  ]
}
```

**Resolution flow:**
1. Step 0: No refs (first step) → executes immediately → returns `{asset_path: "/Game/Materials/M_Test"}`
2. Step 1: Deep-copy params → resolve `$steps[0].data.asset_path` → `/Game/Materials/M_Test` → execute → returns `{node_id: "MaterialExpressionConstant_0"}`
3. Step 2: Deep-copy params → resolve TWO refs → execute → returns `{connected: true}`

### Type Preservation

**CRITICAL:** $ref resolution preserves JSON types. A reference to a number field returns a number, not a string.

```json
// Step 0 returns: {"data": {"count": 5}}
// Step 1 params: {"limit": "$steps[0].data.count"}
// After resolution: {"limit": 5}  ← number, NOT "5" string
```

This prevents silent type conversion bugs where downstream commands expect `TryGetNumberField` but receive a string.

## Escape Mechanism

Literal strings starting with `$steps[` can be escaped with `$$steps[`:

```json
{"params": {"description": "$$steps[0] is a literal string, not a ref"}}
```

After resolution: `{"description": "$steps[0] is a literal string, not a ref"}`

## Error Handling

### stop_on_error: true (Recommended for Atomic Operations)

Execution halts at the first failed step. Response includes all completed results plus the error.

```json
{
  "success": true,
  "data": {
    "results": [
      {"index": 0, "success": true, "data": {...}, "timing_ms": 10.2},
      {"index": 1, "success": true, "data": {...}, "timing_ms": 5.1},
      {"index": 2, "success": false, "error_code": "PIN_NOT_FOUND", "error_message": "Pin 'XYZ' not found", "timing_ms": 1.3}
    ],
    "count": 3,
    "total_timing_ms": 16.6
  }
}
```

Step 2 failed, so steps 3+ were not executed. The agent can inspect completed steps and decide recovery.

### stop_on_error: false (Default, Backward Compatible)

All steps execute regardless of failures. Use for independent operations where partial success is acceptable.

```json
{
  "success": true,
  "data": {
    "results": [
      {"index": 0, "success": true, ...},
      {"index": 1, "success": false, "error_code": "ASSET_NOT_FOUND", ...},
      {"index": 2, "success": true, ...},
      {"index": 3, "success": false, "error_code": "INVALID_FIELD", ...}
    ],
    "count": 4,
    "total_timing_ms": 35.2
  }
}
```

Steps 0 and 2 succeeded despite failures at steps 1 and 3.

### $ref Error Cases

| Case | Error |
|------|-------|
| Future reference: `$steps[5]` from step 3 | `BATCH_REF_RESOLUTION_FAILED: Ref to step 5 out of bounds (current step: 3)` |
| Self-reference: `$steps[3]` from step 3 | `BATCH_REF_RESOLUTION_FAILED: Ref to step 3 out of bounds (current step: 3)` |
| Failed step: `$steps[1]` when step 1 failed | `BATCH_REF_RESOLUTION_FAILED: Ref to failed step 1` |
| Missing field: `$steps[0].data.nonexistent` | `BATCH_REF_RESOLUTION_FAILED: Field 'nonexistent' not found in step 0 data` |
| Malformed: `$steps[]`, `$steps[abc]` | `BATCH_REF_RESOLUTION_FAILED: Malformed ref` |
| Empty path: `$steps[0].data` | `BATCH_REF_RESOLUTION_FAILED: Ref has empty field path` |
| Max depth: Recursion > 10 levels | `BATCH_REF_RESOLUTION_FAILED: Max recursion depth exceeded` |

**Mid-string refs:** If a string *contains* `$steps[` but doesn't *start* with it, a warning is logged but the string passes through unchanged:
```
String field 'description' contains '$steps[' mid-string - this is not resolved. Value: "See step $steps[0] for details"
```

## Advanced Patterns

### Nested Object Resolution

$ref works in nested objects and arrays at any depth (up to 10 levels):

```json
{
  "command": "material.set_node_property",
  "params": {
    "asset_path": "$steps[0].data.asset_path",
    "node_id": "$steps[1].data.node_id",
    "property_name": "DefaultValue",
    "value": {
      "R": "$steps[2].data.red_channel",
      "G": 0.5,
      "B": "$steps[2].data.blue_channel",
      "A": 1.0
    }
  }
}
```

### Array Element References

Reference array elements with index notation:

```json
// Step 0 returns: {"data": {"nodes": [{"id": "Node_0"}, {"id": "Node_1"}]}}
{"params": {"node_id": "$steps[0].data.nodes[1].id"}}
// Resolves to: {"params": {"node_id": "Node_1"}}
```

### Chained References

Step N can reference any earlier step, not just N-1:

```json
[
  {"command": "material.create_material", ...},  // Step 0
  {"command": "material.add_node", ...},          // Step 1
  {"command": "material.add_node", ...},          // Step 2
  {"command": "material.connect", "params": {
    "asset_path": "$steps[0].data.asset_path",   // Ref to step 0
    "source_node": "$steps[1].data.node_id",     // Ref to step 1
    "target_node": "$steps[2].data.node_id"      // Ref to step 2
  }}
]
```

## Performance Characteristics

### Execution Model

- All commands execute sequentially on the Game Thread
- Single `FScopedTransaction` for entire batch (one undo entry)
- Deep-copy params before $ref resolution (original request never mutated)
- `FCortexBatchScope` RAII guard defers `PostEditChange`/`RebuildGraph` until batch end

### Timing

| Batch Size | Typical Duration | Notes |
|------------|------------------|-------|
| 10 commands | 50-100ms | Mostly add_node + connect |
| 50 commands | 200-400ms | Small material graph |
| 127 commands | 800-1500ms | Production material (40 nodes) |
| 200 commands | 1000-2000ms | Max batch size |

**Warning:** If `total_timing_ms > 1000ms`, a warning is logged (expected for large batches).

### Timeout Scaling

Python MCP composite tools scale TCP timeout dynamically:
```python
timeout = max(60, len(commands) * 2)  # 60s minimum, 2s per command
```

This prevents legitimate large batches from timing out.

## Batch-Aware Operations

Material operations check `FCortexCommandRouter::IsInBatch()` to defer expensive operations:

**During batch:**
- `PostEditChange()` — deferred (called once at end via `FCortexBatchScope`)
- `MaterialGraph->RebuildGraph()` — deferred (called once at end)
- `FScopedTransaction` — skipped (batch creates single transaction)

**Benefits:**
- 127-step batch: 125 rebuilds avoided → 5-30s editor freeze prevented
- Single undo entry instead of N entries
- Atomic rollback on Ctrl+Z

## Best Practices

### When to Use Batches

**Use batch with `stop_on_error: true` for:**
- Creating complex assets (materials, blueprints, UI screens)
- Multi-step atomic operations where partial completion is invalid
- Operations with dependencies between steps ($ref wiring)

**Use individual tool calls for:**
- Single operations
- Independent operations where partial success is acceptable
- Interactive workflows where immediate feedback is needed

### Batch Scope

**One batch = one entity.** Don't mix entity creation in a single batch:

**DON'T:**
```json
[
  {"command": "material.create_material", ...},    // Material
  {"command": "material.create_instance", ...},    // Instance (depends on material)
  {"command": "material.create_instance", ...}     // Another instance
]
```

**DO:**
```json
// Batch 1: Create material with nodes/connections
material_compose(...)

// Batch 2: Create instance (depends on batch 1)
material.create_instance(parent_path: result_from_batch_1)

// Batch 3: Create another instance
material.create_instance(parent_path: result_from_batch_1)
```

Cross-entity orchestration is the AI agent's responsibility — tools enforce dependencies naturally.

### Validation

**Validate early in Python layer, not in C++ batch:**
- Required fields
- Node name uniqueness
- Connection validity
- No user params starting with `$steps[`

This prevents expensive batch execution only to fail at step 15 of 50.

### Error Recovery

Composite tools handle cleanup-on-failure:
```python
if batch_failed and step_0_succeeded:
    # Partial asset exists, delete it
    connection.send_command("material.delete_material", {"asset_path": asset_path})
    return {"success": False, "recovery_action": {"action": "deleted_partial", "path": asset_path}}
```

This prevents orphaned partial assets that block retries with `ASSET_ALREADY_EXISTS`.

## Limitations

**Not Supported:**
- Nested batch commands (returns `BATCH_RECURSION_BLOCKED`)
- Mid-string $ref interpolation (`"prefix_$steps[0].data.value_suffix"` logs warning, not resolved)
- Conditional execution (if/else branching)
- Parallel step execution
- Automatic rollback on failure (use cleanup-on-failure pattern instead)

**Deferred to Feature Requests:**
- Automatic batch splitting (Python auto-splits batches > 200 into phases)
- Configurable MaxBatchSize via `UCortexSettings`
- Dry run mode (validate batch without executing)
- Rollback/transactional batch (undo completed steps on error)

## Examples

### Example 1: Pulsating Gradient Material (9 nodes, 24 steps)

```json
{
  "command": "batch",
  "params": {
    "stop_on_error": true,
    "commands": [
      {"command": "material.create_material", "params": {"name": "M_PulsatingGradient", "asset_path": "/Game/Materials/"}},
      {"command": "material.add_node", "params": {"asset_path": "$steps[0].data.asset_path", "expression_class": "MaterialExpressionConstant3Vector"}},
      {"command": "material.set_node_property", "params": {"asset_path": "$steps[0].data.asset_path", "node_id": "$steps[1].data.node_id", "property_name": "Constant", "value": [1.0, 0.0, 0.0]}},
      {"command": "material.add_node", "params": {"asset_path": "$steps[0].data.asset_path", "expression_class": "MaterialExpressionConstant3Vector"}},
      {"command": "material.set_node_property", "params": {"asset_path": "$steps[0].data.asset_path", "node_id": "$steps[3].data.node_id", "property_name": "Constant", "value": [0.0, 0.0, 1.0]}},
      {"command": "material.add_node", "params": {"asset_path": "$steps[0].data.asset_path", "expression_class": "MaterialExpressionTextureCoordinate"}},
      {"command": "material.add_node", "params": {"asset_path": "$steps[0].data.asset_path", "expression_class": "MaterialExpressionLinearInterpolate"}},
      {"command": "material.connect", "params": {"asset_path": "$steps[0].data.asset_path", "source_node": "$steps[1].data.node_id", "source_output": "0", "target_node": "$steps[6].data.node_id", "target_input": "A"}},
      {"command": "material.connect", "params": {"asset_path": "$steps[0].data.asset_path", "source_node": "$steps[3].data.node_id", "source_output": "0", "target_node": "$steps[6].data.node_id", "target_input": "B"}},
      {"command": "material.connect", "params": {"asset_path": "$steps[0].data.asset_path", "source_node": "$steps[5].data.node_id", "source_output": "0", "target_node": "$steps[6].data.node_id", "target_input": "Alpha"}},
      {"command": "material.add_node", "params": {"asset_path": "$steps[0].data.asset_path", "expression_class": "MaterialExpressionTime"}},
      {"command": "material.add_node", "params": {"asset_path": "$steps[0].data.asset_path", "expression_class": "MaterialExpressionSine"}},
      {"command": "material.connect", "params": {"asset_path": "$steps[0].data.asset_path", "source_node": "$steps[10].data.node_id", "source_output": "0", "target_node": "$steps[11].data.node_id", "target_input": "Input"}},
      {"command": "material.add_node", "params": {"asset_path": "$steps[0].data.asset_path", "expression_class": "MaterialExpressionScalarParameter"}},
      {"command": "material.set_node_property", "params": {"asset_path": "$steps[0].data.asset_path", "node_id": "$steps[13].data.node_id", "property_name": "ParameterName", "value": "GlowStrength"}},
      {"command": "material.set_node_property", "params": {"asset_path": "$steps[0].data.asset_path", "node_id": "$steps[13].data.node_id", "property_name": "DefaultValue", "value": 2.0}},
      {"command": "material.add_node", "params": {"asset_path": "$steps[0].data.asset_path", "expression_class": "MaterialExpressionMultiply"}},
      {"command": "material.connect", "params": {"asset_path": "$steps[0].data.asset_path", "source_node": "$steps[11].data.node_id", "source_output": "0", "target_node": "$steps[16].data.node_id", "target_input": "A"}},
      {"command": "material.connect", "params": {"asset_path": "$steps[0].data.asset_path", "source_node": "$steps[13].data.node_id", "source_output": "0", "target_node": "$steps[16].data.node_id", "target_input": "B"}},
      {"command": "material.add_node", "params": {"asset_path": "$steps[0].data.asset_path", "expression_class": "MaterialExpressionMultiply"}},
      {"command": "material.connect", "params": {"asset_path": "$steps[0].data.asset_path", "source_node": "$steps[6].data.node_id", "source_output": "0", "target_node": "$steps[19].data.node_id", "target_input": "A"}},
      {"command": "material.connect", "params": {"asset_path": "$steps[0].data.asset_path", "source_node": "$steps[16].data.node_id", "source_output": "0", "target_node": "$steps[19].data.node_id", "target_input": "B"}},
      {"command": "material.connect", "params": {"asset_path": "$steps[0].data.asset_path", "source_node": "$steps[19].data.node_id", "source_output": "0", "target_node": "MaterialResult", "target_input": "EmissiveColor"}},
      {"command": "material.connect", "params": {"asset_path": "$steps[0].data.asset_path", "source_node": "$steps[6].data.node_id", "source_output": "0", "target_node": "MaterialResult", "target_input": "BaseColor"}},
      {"command": "material.auto_layout", "params": {"asset_path": "$steps[0].data.asset_path"}}
    ]
  }
}
```

**Result:** Material created with 9 nodes and 10 connections in ~850ms, single undo entry, automatic layout applied.

### Example 2: DataTable Population (Batch Query)

```json
{
  "command": "batch",
  "params": {
    "stop_on_error": false,
    "commands": [
      {"command": "data.query_datatable", "params": {"table": "/Game/Data/DT_Enemies", "filter": {"Type": "Boss"}}},
      {"command": "data.query_datatable", "params": {"table": "/Game/Data/DT_Enemies", "filter": {"Type": "Minion"}}},
      {"command": "data.query_datatable", "params": {"table": "/Game/Data/DT_Loot", "filter": {"Rarity": "Legendary"}}}
    ]
  }
}
```

Independent queries — partial success acceptable, so `stop_on_error: false`.

## See Also

- **Material Composite Tools:** `resources/material-patterns.md`
- **MCP Tool Reference:** `resources/mcp-tool-reference.md`
- **MCP Architecture:** `resources/mcp-architecture.md`
- **Testing Guide:** `resources/testing-guide.md`
