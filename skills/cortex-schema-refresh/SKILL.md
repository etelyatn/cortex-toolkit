---
name: cortex-schema-refresh
description: Use when user wants to refresh project schema files, when .cortex/schema/ is missing or stale, or when data structures have changed
---

# Refresh Project Schema

Generate LLM-readable schema files in `.cortex/schema/`.

## Filtering Rule

**Only include game project classes and assets.** Exclude:
- Engine classes (`/Engine/`, `Engine/Source/Runtime/`, `Engine/Plugins/`)
- Marketplace and third-party plugin classes (any path under `Plugins/` that is not the project's own plugin)
- Editor-only utility classes not relevant to gameplay

Keep only classes and assets under `/Game/` (Content/) and the project's own source modules.

## Steps

1. Check if the Unreal Editor is running (use `core_cmd(command="get_status")`)
2. If not running, inform the user that the editor must be open
3. Call `schema_generate` with `domain: "all"`
4. After generation, review `.cortex/schema/` output and remove or flag any engine-only or marketplace noise that leaked through
5. Report results: which files were generated, any errors
6. Read `.cortex/schema/_catalog.md` to verify the output
