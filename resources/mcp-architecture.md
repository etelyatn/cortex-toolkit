# MCP Architecture Reference

How UnrealCortex connects AI coding agents to the Unreal Editor.

## Architecture

```
AI Agent → MCP Server (Python) → TCP → CortexCore (C++ UE Plugin) → Unreal Editor
```

## TCP Protocol

- **Transport:** Line-delimited JSON over TCP
- **Address:** `127.0.0.1:{port}`
- **Port discovery:** Read from `Saved/CortexPort-{PID}.txt` (written by CortexCore on startup)
- **Default port:** 8742, auto-increments if busy (supports multiple editors)

Commands are namespaced: `{domain}.{command}`

```json
{"command": "data.list_datatables", "params": {"path": "/Game/Data"}}
```

Built-in commands (no namespace): `get_status`, `get_capabilities`

## MCP Server

- **Location:** `Plugins/UnrealCortex/MCP/src/cortex_mcp/`
- **Tools:** explicit registration from `Plugins/UnrealCortex/MCP/src/cortex_mcp/tools/`
- **Run:** `uv run --directory Plugins/UnrealCortex/MCP cortex-mcp`
- **Config:** `.mcp.json` in project root

## Connection Guard (PreToolUse Hook)

The `cortex-core` plugin includes a PreToolUse hook that gates every `cortex_mcp` tool call, ensuring the editor and CortexCore TCP server are ready before any MCP command executes.

**Fast path (~50ms):** Port file exists + TCP socket responds → hook exits silently, no delay.

**Auto-start path:** If the editor is not running, the hook:
1. Acquires a lock file to prevent parallel startup races (Claude batches MCP calls)
2. Resolves the engine path from `UE_56_PATH` or `.cortex/config.yaml`
3. Launches the editor with `-nosplash -unattended -nopause`
4. Two-phase polls for up to 180s (silent wait → process-alive checks)
5. Exits 0 once `CortexPort-{PID}.txt` is written and TCP responds

**Failure path:** If the editor cannot be started or times out, the hook exits with code 2 and directs the agent to present options to the user (start manually, fix config, or abort).

## Port Re-discovery

The MCP TCP client automatically re-reads `Saved/CortexPort-{PID}.txt` on reconnect. If the editor restarts on a different port (e.g., another editor instance was already using the default), the client picks up the new port without requiring a manual restart.

## Caching

MCP tools implement intelligent caching:
- Schema/structure data: 30 min TTL
- List operations: 5 min TTL
- Dynamic data: 2 min TTL
- Write operations: auto-invalidate related caches
- Manual: `refresh_cache` clears everything

## MCP Benchmark Testing

Three-layer integration testing covers both live editor-backed validation and Python-side tool tests. Layers 1 and 3 require a running editor; Layer 2 now includes a live editor-backed StateTree scenario plus separate mocked StateTree composite coverage.

StateTree coverage:
- Router domain: `statetree_cmd`
- Composite: `statetree_compose`
- Coverage:
  - live FastMCP scenario for StateTree create/inspect/validate/compile flow
  - mocked Python composite wrapper/registration and command translation for StateTree update flows

| Layer | File(s) | What It Tests |
|-------|---------|---------------|
| 1: TCP E2E | `test_e2e.py`, `test_level_e2e.py`, `test_editor_e2e.py`, `test_class_defaults.py`, `test_material_composites_e2e.py` | Direct TCP commands per domain (CRUD + error cases) |
| 2: MCP Scenarios | `test_mcp_scenarios.py`, `test_blueprint_composites.py`, `test_material_composites.py`, `test_umg_composites.py`, `test_statetree_composites.py` | Cross-domain workflows via FastMCP client, including live StateTree structure coverage; `test_statetree_composites.py` separately covers mocked wrapper registration and translation |
| 3: Claude Skill | `/mcp-benchmark` | AI-driven real-world validation with timing |

Tests live in `Plugins/UnrealCortex/MCP/tests/`. Run with:

```bash
# Layer 1 — all TCP E2E tests
cd Plugins/UnrealCortex/MCP && uv run pytest tests/test_e2e.py tests/test_level_e2e.py tests/test_editor_e2e.py -v

# Layer 2 — cross-domain scenarios
cd Plugins/UnrealCortex/MCP && uv run pytest tests/test_mcp_scenarios.py -v

# StateTree composites
cd Plugins/UnrealCortex/MCP && uv run pytest tests/test_statetree_composites.py -v

# Layer 3 — Claude Code skill
/mcp-benchmark
```

See `resources/testing-guide.md` for comprehensive test file map and pytest markers.
