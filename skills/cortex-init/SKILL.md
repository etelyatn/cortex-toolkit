---
name: cortex-init
description: Use when setting up a new Unreal Engine project for AI-assisted development, when .cortex/ directory is missing, or when MCP connection needs configuration
---

# Cortex Init

Sets up a UE project for AI-assisted development with UnrealCortex.

## Steps

### 1. Validate UnrealCortex Plugin

Check for `UnrealCortex.uplugin` in any of these locations (in order):
1. `Plugins/UnrealCortex/UnrealCortex.uplugin`
2. `Plugins/Developer/UnrealCortex/UnrealCortex.uplugin`

If neither exists, do a recursive glob search: `Plugins/**/UnrealCortex.uplugin` (catches any other subfolder layout).

Use whichever path exists. Store the **directory** containing the `.uplugin` file as `{plugin_root}` for use in Step 3.

If not found in any location, tell the user to add the UnrealCortex submodule:
```
git submodule add https://github.com/etelyatn/UnrealCortex Plugins/UnrealCortex
```

#### 1b. Verify Plugin Is Enabled in .uproject

Find the `.uproject` file in the project root and parse its `Plugins` array:

```bash
UPROJECT=$(ls *.uproject 2>/dev/null | head -1)
if [ -n "$UPROJECT" ]; then
  PLUGIN_STATUS=$(python3 -c "
import json, sys
with open(sys.argv[1], encoding='utf-8') as f:
    data = json.load(f)
plugins = data.get('Plugins', [])
match = [p for p in plugins if p.get('Name') == 'UnrealCortex']
if not match:
    print('missing')
elif not match[0].get('Enabled', False):
    print('disabled')
else:
    print('enabled')
" "$UPROJECT" 2>/dev/null || python -c "
import json, sys
with open(sys.argv[1], encoding='utf-8') as f:
    data = json.load(f)
plugins = data.get('Plugins', [])
match = [p for p in plugins if p.get('Name') == 'UnrealCortex']
if not match:
    print('missing')
elif not match[0].get('Enabled', False):
    print('disabled')
else:
    print('enabled')
" "$UPROJECT" 2>/dev/null || echo "parse_error")
fi
```

If `enabled` or `missing`: Continue to Step 2. Local plugins placed in the project's `Plugins/` folder are enabled by default in Unreal Engine — they don't need an explicit entry in the `.uproject` file.

If `disabled`: Print this message and STOP. Do not proceed to create `.cortex/` until the plugin is enabled.
```
UnrealCortex plugin is explicitly disabled in {UPROJECT}.

To enable it:
1. Open the editor: Edit -> Plugins -> search "UnrealCortex" -> Enable
2. Accept the beta warning if prompted
3. Restart the editor
4. Re-run cortex-init

Alternatively, edit {UPROJECT} and change "Enabled": false to "Enabled": true for the UnrealCortex entry.
Then restart the editor and re-run cortex-init.
```

If `parse_error`: Warn ("Could not parse {UPROJECT} - verify manually that UnrealCortex is enabled") and continue.

If no `.uproject` file found: Warn ("No .uproject file found - you may be running from a subdirectory") and continue.

### 2. Detect Unreal Engine

Find the engine installation in order:
1. Check common paths: `C:/Program Files/Epic Games/UE_5.*`
2. Check `$UE_PATH` environment variable
3. Ask the user for the path

Verify the path exists and contains `Engine/Binaries/Win64/UnrealEditor.exe`.

### 3. Detect Enabled Domains

Read `{plugin_root}/UnrealCortex.uplugin` (detected in Step 1) and extract module names.
Map modules to domains:
- `CortexData` → `data`
- `CortexBlueprint` + `CortexGraph` → `blueprint`
- `CortexMaterial` → `material`
- `CortexUMG` → `umg`
- `CortexLevel` → `level`
- `CortexQA` → `qa`
- `CortexReflect` → `reflect`
- `CortexStateTree` → `statetree`
- `CortexCore` → (foundation, no domain file needed)
- `CortexEditor` → (shared infrastructure, no domain file needed)

### 4. Create .cortex/ Directory

Create the following structure:

`.cortex/config.yaml`:
```yaml
engine:
  path: "<detected path>"
  version: "<detected version>"

# Per-machine overrides belong in .cortex/config.local.yaml.
# Keep config.yaml for shared project defaults.

domains:
  - data
  # add detected domains

references:
  # game_design: docs/design/gdd.md
```

Ensure `.gitignore` contains:
```gitignore
.cortex/config.local.yaml
```

Do not create `.cortex/config.local.yaml` during init unless the user explicitly asks for a local override. The file is for each developer's private machine-specific values, most commonly:
```yaml
engine:
  path: "C:/Path/To/This/Machine/UE"
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
- `statetree.md`: StateTree hierarchy conventions, schema choices, transition/tag rules

### 5. Configure MCP

Use `.mcp.json` as the assistant-agnostic MCP config for this project.

Before writing, resolve two absolute paths:

- `{project_root}` — the absolute path of the current working directory. Use:
  ```bash
  uv run python -c "import os; print(os.path.abspath('.').replace(chr(92), '/'))"
  ```
  This gives the OS-native path in forward-slash form (e.g. `D:/UnrealProjects/MyGame`), which works correctly for both Claude Code and native Windows MCP clients like Cursor or Windsurf. Do not use `pwd` — it returns POSIX paths (`/d/UnrealProjects/MyGame`) that native Windows processes cannot resolve.

- `{mcp_dir}` — `{project_root}/{plugin_root}/MCP`, where `{plugin_root}` is the directory detected in Step 1 (e.g. `Plugins/UnrealCortex` or `Plugins/Developer/UnrealCortex`).

If `.mcp.json` is missing, create it with:
```json
{
  "mcpServers": {
    "cortex_mcp": {
      "command": "uv",
      "args": ["run", "--directory", "{mcp_dir}", "cortex-mcp"],
      "env": {
        "CORTEX_PROJECT_DIR": "{project_root}"
      }
    }
  }
}
```

If `.mcp.json` already exists:
- Preserve all existing top-level keys.
- Preserve all existing `mcpServers` entries.
- Upsert only `mcpServers.cortex_mcp`, replacing the entire object with the resolved values above. Do not carry forward field values from the existing entry.
- Do not remove or rewrite unrelated MCP server configs.

### 6. Inject LLM Context

**This step is required — do not skip it.** Ask the user for each file (CLAUDE.md default yes, AGENTS.md default ask):

> "Inject Cortex Toolkit context block into `CLAUDE.md`? (y/n) [y]"
> "Create/update `AGENTS.md` with Cortex Toolkit context? (y/n)"

**For each approved file, follow this sequence:**

**A. Check writeability**
Attempt the write; if a write error occurs, report "Cannot write to {file} — {error}" and skip. Do not pre-check with stat.

**B. Sentinel guard**
Search the file for `<!-- cortex-toolkit:`.
- Not found → proceed to inject.
- Found matching current version (`<!-- cortex-toolkit:v1 -->`) → skip, report "already present (v1)".
- Found with different version → warn: "Existing Cortex Toolkit block found (older version). Replace it? (y/n)". If yes, remove old block: starting from the sentinel line, delete until the next `---` or root-level `##` heading found *after* the sentinel, or end of file — whichever comes first; if no, skip.

**C. Build filtered block**
Read the canonical template:
- For `CLAUDE.md`: `{toolkit-root}/templates/claude-block.md`
- For `AGENTS.md`: `{toolkit-root}/templates/agents-block.md`

`{toolkit-root}` resolves as:
1. If `CLAUDE_PLUGIN_ROOT` env var is set (marketplace install) → use that path.
2. Otherwise → go two directories up from this skill file (`skills/cortex-init/SKILL.md` → toolkit root).

Strip the first line of the template (the `<!-- Template: ... -->` header comment) — it is metadata for maintainers, not content for injection.

Filter the table rows to only the domains detected in Step 3, using this key-to-label mapping:

| Detected domain key | Table row label |
|---------------------|-----------------|
| `blueprint`         | `Blueprint`     |
| `data`              | `Data`          |
| `level`             | `Level`         |
| `material`          | `Material`      |
| `statetree`         | `StateTree`     |
| `umg`               | `UI`            |
| `qa`                | `QA`            |
| `reflect`           | `Reflect`       |

Remove any row whose label is not matched by a detected domain key. Always keep the table header and separator rows.

**D. Inject**
- If file exists → append the filtered block preceded by a blank line. Note in output: "Block appended at end of file — you may want to relocate it within the file."
- If file does not exist → create it containing only the block.

**E. Record result** for Step 7 summary.

### 7. Print Summary

Report:
- Engine path and version
- Local override support: `.cortex/config.local.yaml` ignored by VCS
- Detected domains
- Created files
- MCP configured: `CORTEX_PROJECT_DIR={project_root}`, `--directory={mcp_dir}`
- Context injection:
  - CLAUDE.md: injected (N domain rows) / already present / skipped
  - AGENTS.md: injected (N domain rows) / already present / skipped / not requested
- Recommended next actions:
  1. Fill in `.cortex/context.md` with project-specific goals and conventions.
  2. Start/verify the editor with the Cortex editor workflow (`cortex-editor`), then check health with `cortex-status`.
  3. Generate project knowledge with `cortex-schema-refresh` and a CortexReflect scan/rebuild workflow.
  4. Review each `.cortex/domains/*.md` file and add domain-specific conventions, asset locations, and safety rules.
  5. If any detected domain is missing at runtime, compare `.cortex/config.yaml`, `UnrealCortex.uplugin`, and registered runtime domains from the status workflow.
