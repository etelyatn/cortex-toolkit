# MCP Protocol Reference

How UnrealCortex connects AI coding agents to the Unreal Editor.

## Architecture

```
AI Agent → MCP Server (Python) → TCP → CortexCore (C++ UE Plugin) → Unreal Editor
```

## TCP Protocol

- **Transport:** Line-delimited JSON over TCP
- **Address:** `127.0.0.1:{port}`
- **Port discovery:** Read from `Saved/CortexPort.txt` (written by CortexCore on startup)
- **Default port:** 8742, auto-increments if busy (supports multiple editors)

## Command Format

Commands are namespaced: `{domain}.{command}`

```json
{"command": "data.list_datatables", "params": {"path": "/Game/Data"}}
```

Built-in commands (no namespace): `get_status`, `get_capabilities`

## MCP Server

- **Location:** `Plugins/UnrealCortex/MCP/src/cortex_mcp/`
- **Tools:** `Plugins/UnrealCortex/MCP/tools/{domain}/`
- **Run:** `uv run --directory Plugins/UnrealCortex/MCP cortex-mcp`
- **Config:** `.mcp.json` in project root

## Available Domains and Tools

### Core (no namespace)
- `get_status` — connection health, registered domains
- `get_data_catalog` — unified project data overview (cached 10 min)
- `refresh_cache` — clear all cached MCP responses
- `batch` — execute multiple commands sequentially with $ref resolution

#### Batch Command

Execute multiple commands in a single round-trip with cross-step data references.

**Parameters:**
- `commands` (array, required): Array of command objects with `command` and `params` fields
- `stop_on_error` (bool, default `false`): Halt execution at first failure

**Limits:**
- MaxBatchSize: 200 commands per batch
- Max message size: 2MB

**$ref Resolution:**
String parameter values matching `$steps[N].data.field` are resolved from previous step results before execution:

```json
{
  "command": "batch",
  "params": {
    "stop_on_error": true,
    "commands": [
      {"command": "material.create_material", "params": {"name": "M_Test", "asset_path": "/Game/Materials/"}},
      {"command": "material.add_node", "params": {
        "asset_path": "$steps[0].data.asset_path",
        "expression_class": "MaterialExpressionConstant"
      }}
    ]
  }
}
```

**$ref rules:**
- Must be entire string value (no mid-string interpolation)
- Only references to previous steps (N < current step)
- Type-preserving (numbers stay numbers, bools stay bools)
- Escape literal `$steps[` with `$$steps[`
- Works in nested objects/arrays (max depth: 10)

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {"index": 0, "success": true, "data": {...}, "timing_ms": 12.3},
      {"index": 1, "success": true, "data": {...}, "timing_ms": 2.1}
    ],
    "count": 2,
    "total_timing_ms": 14.4
  }
}
```

See `cortex-toolkit/cortex-core/resources/batch-pipeline-guide.md` for comprehensive reference.

### Data (`data.*`)
- DataTables: `list_datatables`, `get_datatable_schema`, `query_datatable`, `get_datatable_row`, `add_datatable_row`, `update_datatable_row`, `delete_datatable_row`, `search_datatable_content`, `import_datatable_json`, `batch_query`, `get_struct_schema`
- GameplayTags: `list_gameplay_tags`, `validate_gameplay_tag`, `register_gameplay_tag`, `register_gameplay_tags`, `resolve_tags`
- DataAssets: `list_data_assets`, `get_data_asset`, `update_data_asset`
- CurveTables: `list_curve_tables`, `get_curve_table`, `update_curve_table_row`
- StringTables: `list_string_tables`, `get_translations`, `set_translation`
- Search: `search_assets`

### Blueprint (`bp.*`)
- Assets: `create_blueprint`, `list_blueprints`, `get_blueprint_info`, `delete_blueprint`, `duplicate_blueprint`, `compile_blueprint`, `save_blueprint`
- Structure: `add_blueprint_variable`, `remove_blueprint_variable`, `add_blueprint_function`

### Graph (`graph.*`)
- `graph_list_graphs`, `graph_list_nodes`, `graph_get_node`, `graph_add_node`, `graph_remove_node`, `graph_connect`, `graph_disconnect`

### UMG (`umg.*`)
- Tree: `add_widget`, `remove_widget`, `reparent`, `get_tree`, `get_widget`, `list_widget_classes`, `duplicate_widget`
- Properties: `set_color`, `set_text`, `set_font`, `set_brush`, `set_padding`, `set_anchor`, `set_alignment`, `set_size`, `set_visibility`, `set_property`, `get_property`, `get_schema`
- Animations: `create_animation`, `list_animations`, `remove_animation`

## Connection Guard (PreToolUse Hook)

The `cortex-core` plugin includes a PreToolUse hook that gates every `cortex_mcp` tool call, ensuring the editor and CortexCore TCP server are ready before any MCP command executes.

**Fast path (~50ms):** Port file exists + TCP socket responds → hook exits silently, no delay.

**Auto-start path:** If the editor is not running, the hook:
1. Acquires a lock file to prevent parallel startup races (Claude batches MCP calls)
2. Resolves the engine path from `UE_56_PATH` or `.cortex/config.yaml`
3. Launches the editor with `-nosplash -unattended -nopause`
4. Two-phase polls for up to 180s (silent wait → process-alive checks)
5. Exits 0 once `CortexPort.txt` is written and TCP responds

**Failure path:** If the editor cannot be started or times out, the hook exits with code 2 and directs the agent to present options to the user (start manually, fix config, or abort).

## Port Re-discovery

The MCP TCP client automatically re-reads `Saved/CortexPort.txt` on reconnect. If the editor restarts on a different port (e.g., another editor instance was already using the default), the client picks up the new port without requiring a manual restart.

## Caching

MCP tools implement intelligent caching:
- Schema/structure data: 30 min TTL
- List operations: 5 min TTL
- Dynamic data: 2 min TTL
- Write operations: auto-invalidate related caches
- Manual: `refresh_cache` clears everything
