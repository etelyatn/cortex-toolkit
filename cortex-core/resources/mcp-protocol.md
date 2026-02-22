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

### Editor (composite tools — no namespace prefix)
- PIE lifecycle: `start_pie_session`, `stop_pie_session`, `get_pie_state`, `pause_pie`, `resume_pie`, `restart_pie`
- Viewport: `get_viewport_info`, `capture_screenshot`, `set_viewport_camera`, `focus_actor`, `set_viewport_mode`
- Utilities: `get_editor_state`, `get_recent_logs`, `execute_console_command`, `set_time_dilation`, `get_world_info`
- Input injection (requires active PIE): `press_key`, `run_input_sequence`
- Editor lifecycle: `shutdown_editor`, `restart_editor`

#### Input Injection Tools

`press_key` — inject a single key event into the active PIE session:
- `key` (str): UE key name — `"W"`, `"SpaceBar"`, `"LeftShift"`, `"Enter"`, `"Escape"`, `"F1"`, `"LeftMouseButton"`. Case-sensitive.
- `action` (str): `"tap"` (press + timed release), `"press"` (hold), or `"release"`. Default `"tap"`.
- `duration_ms` (int): Hold duration for tap. Default 100.

`run_input_sequence` — execute a timed multi-step input sequence during PIE (deferred):
- `steps` (list): Each step has `at_ms` (int, timing offset from start) and `kind` (`"key"`, `"mouse"`, or `"action"`).
  - `kind="key"`: `key` (str), `action` (str, default `"tap"`), `duration_ms` (int, default 100)
  - `kind="mouse"`: `action` (`"click"`, `"move"`, or `"scroll"`), `button` (str, for click), `x`/`y` (float), `delta` (float, for scroll)
  - `kind="action"`: `action_name` (str), `value` (float, default 1.0) — Enhanced Input action injection
- `timeout` (float): Total wait time for sequence completion. Default 60s.

Example — walk and jump:
```json
{
  "steps": [
    {"at_ms": 0,    "kind": "key", "key": "W",        "action": "press"},
    {"at_ms": 500,  "kind": "key", "key": "SpaceBar", "action": "tap"},
    {"at_ms": 1000, "kind": "key", "key": "W",        "action": "release"}
  ]
}
```

**Constraint:** Only one `run_input_sequence` should run at a time — concurrent sequences share a single callback slot (see ED-001 in `docs/tech-debt/cortex-editor-tech-debt.md`).

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
