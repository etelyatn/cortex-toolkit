---
name: cortex-schema-refresh
description: Use when user wants to refresh project schema files, when .cortex/schema/ is missing or stale, or when data structures have changed
---

# Refresh Project Schema

Generate LLM-readable schema files in `.cortex/schema/`.

## Steps

1. Check if the Unreal Editor is running (use `get_status` MCP tool)
2. If not running, inform the user that the editor must be open
3. Call `generate_project_schema` MCP tool with `domain: "all"`
4. Report results: which files were generated, any errors
5. Read `.cortex/schema/_catalog.md` to verify the output
