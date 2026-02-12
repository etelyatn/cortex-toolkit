---
name: cortex-init
description: Use when setting up a new Unreal Engine project for AI-assisted development, when .cortex/ directory is missing, or when MCP connection needs configuration
---

# Cortex Init

Sets up a UE project for AI-assisted development with UnrealCortex.

## Steps

### 1. Validate UnrealCortex Plugin

Check that `Plugins/UnrealCortex/` exists and contains `UnrealCortex.uplugin`.

If missing, tell the user to add the UnrealCortex submodule:
```
git submodule add https://github.com/etelyatn/UnrealCortex Plugins/UnrealCortex
```

### 2. Detect Unreal Engine

Find the engine installation in order:
1. Check `$UE_56_PATH` environment variable
2. Check common paths: `C:/Program Files/Epic Games/UE_5.*`
3. Ask the user for the path

Verify the path exists and contains `Engine/Binaries/Win64/UnrealEditor.exe`.

### 3. Detect Enabled Domains

Read `Plugins/UnrealCortex/UnrealCortex.uplugin` and extract module names.
Map modules to domains:
- `CortexData` → `data`
- `CortexBlueprint` + `CortexGraph` → `blueprint`
- `CortexUMG` → `umg`

### 4. Create .cortex/ Directory

Create the following structure:

`.cortex/config.yaml`:
```yaml
engine:
  path: "<detected path>"
  version: "<detected version>"

domains:
  - data
  # add detected domains

references:
  # game_design: docs/design/gdd.md
```

`.cortex/context.md`:
```markdown
# Project Context

<!-- Describe your game/project here. Agents read this at session start. -->

## Key Systems
<!-- List major systems: quest system, inventory, combat, etc. -->

## Conventions
<!-- Project-wide naming conventions, patterns, rules -->
```

Create `.cortex/domains/` with a template for each detected domain:
- `data.md`: tables, balance rules, struct descriptions
- `blueprints.md`: BP conventions, key blueprints, class hierarchy
- `umg.md`: widget conventions, screen list, UI patterns

### 5. Configure MCP

Check `.mcp.json` exists. If not, create it:
```json
{
  "mcpServers": {
    "cortex_mcp": {
      "command": "uv",
      "args": ["run", "--directory", "Plugins/UnrealCortex/MCP", "cortex-mcp"],
      "env": {
        "CORTEX_PROJECT_DIR": "."
      }
    }
  }
}
```

### 6. Print Summary

Report:
- Engine path and version
- Detected domains
- Created files
- Next steps: "Fill in .cortex/context.md with your project details"
