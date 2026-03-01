# Cortex Toolkit

You are working with a project that uses UnrealCortex — an MCP bridge between AI coding assistants and Unreal Engine.

## Available MCP Tools

The `cortex_mcp` server (configured in `.mcp.json`) provides tools organized by domain:
- **Core:** `get_status`, `get_capabilities`, `batch_query`
- **Data:** DataTables, DataAssets, CurveTables, StringTables, GameplayTags
- **Blueprint:** Blueprint CRUD, graph operations, compilation
- **Material:** Materials, instances, parameter collections, expression graphs
- **Level:** Actor lifecycle, transforms, components, queries
- **UI (UMG):** Widget hierarchy, properties, animations
- **QA:** Gameplay scenarios, assertions, world state queries
- **Reflect:** Class hierarchy, cross-references, overrides
- **Editor:** PIE lifecycle, screenshots, viewport, input injection

## Project Memory

Read `.cortex/config.yaml` for engine path and active domains.
Read `.cortex/context.md` for project-specific conventions.
Read `.cortex/domains/*.md` for domain-specific knowledge.
Read `.cortex/schema/` for DataTable schemas and struct definitions.

## Before Using MCP Tools

The Unreal Editor must be running with the CortexCore plugin loaded. Use `get_status` to verify connectivity before starting work.
