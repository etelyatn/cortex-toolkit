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

#### 1b. Verify Plugin Is Enabled in .uproject

Find the `.uproject` file in the project root and parse its `Plugins` array:

```bash
UPROJECT=$(ls *.uproject 2>/dev/null | head -1)
if [ -n "$UPROJECT" ]; then
  PLUGIN_STATUS=$(python3 -c "
import json
with open('$UPROJECT', encoding='utf-8') as f:
    data = json.load(f)
plugins = data.get('Plugins', [])
match = [p for p in plugins if p.get('Name') == 'UnrealCortex']
if not match:
    print('missing')
elif not match[0].get('Enabled', False):
    print('disabled')
else:
    print('enabled')
" 2>/dev/null || echo "parse_error")
fi
```

If `enabled`: Continue to Step 2.

If `missing` or `disabled`: Print this message and STOP. Do not proceed to create `.cortex/` until the plugin is enabled.
```
UnrealCortex plugin is not enabled in {UPROJECT}.

To enable it:
1. Open the editor: Edit -> Plugins -> search "UnrealCortex" -> Enable
2. Accept the beta warning if prompted
3. Restart the editor
4. Re-run cortex-init

Alternatively, edit {UPROJECT}:
- If a "Plugins" array exists, add to it: { "Name": "UnrealCortex", "Enabled": true }
- If no "Plugins" key exists, add at the top level: "Plugins": [{ "Name": "UnrealCortex", "Enabled": true }]
Then restart the editor and re-run cortex-init.
```

If `parse_error`: Warn ("Could not parse {UPROJECT} - verify manually that UnrealCortex is enabled") and continue.

If no `.uproject` file found: Warn ("No .uproject file found - you may be running from a subdirectory") and continue.

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
- `CortexMaterial` → `material`
- `CortexUMG` → `umg`
- `CortexLevel` → `level`
- `CortexQA` → `qa`
- `CortexReflect` → `reflect`
- `CortexCore` → (foundation, no domain file needed)
- `CortexEditor` → (shared infrastructure, no domain file needed)

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
- `data.md`: DataTable schemas, balance rules, struct descriptions, GameplayTag conventions
- `blueprints.md`: Blueprint conventions, key Blueprints, class hierarchy, graph patterns
- `material.md`: material conventions, instance hierarchies, parameter collection usage
- `umg.md`: widget conventions, screen inventory, UI style guide
- `level.md`: actor conventions, level structure, streaming setup, organization rules
- `qa.md`: test scenarios, assertion patterns, gameplay test conventions
- `reflect.md`: class hierarchy notes, cross-reference patterns, scan conventions

### 5. Configure MCP

Use `.mcp.json` as the assistant-agnostic MCP config for this project.

If `.mcp.json` is missing, create it with:
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

If `.mcp.json` already exists:
- Preserve all existing top-level keys.
- Preserve all existing `mcpServers` entries.
- Upsert only `mcpServers.cortex_mcp` with the expected value above.
- Do not remove or rewrite unrelated MCP server configs.

### 6. Print Summary

Report:
- Engine path and version
- Detected domains
- Created files
- Next steps: "Fill in .cortex/context.md with your project details"
