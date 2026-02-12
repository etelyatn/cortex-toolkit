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

## Caching

MCP tools implement intelligent caching:
- Schema/structure data: 30 min TTL
- List operations: 5 min TTL
- Dynamic data: 2 min TTL
- Write operations: auto-invalidate related caches
- Manual: `refresh_cache` clears everything
