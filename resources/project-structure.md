# UE Project Structure

Standard layout for UnrealCortex-powered projects.

## Directory Layout

```
ProjectRoot/
├── .cortex/                    ← project memory (AI context)
│   ├── config.yaml
│   ├── context.md
│   └── domains/
├── .mcp.json                   ← MCP server configuration
├── Config/                     ← UE config files
│   └── Tags/                   ← GameplayTag .ini files
├── Content/                    ← UE assets
│   ├── Blueprints/             ← Blueprint assets
│   ├── Data/                   ← DataTables, DataAssets, CurveTables
│   ├── Materials/              ← Materials, instances
│   ├── UI/                     ← UMG widget blueprints
│   └── Temp/                   ← test-generated assets (git-ignored)
├── Plugins/
│   └── UnrealCortex/           ← submodule
│       ├── Source/
│       │   ├── CortexCore/
│       │   ├── CortexData/
│       │   ├── CortexGraph/
│       │   ├── CortexBlueprint/
│       │   ├── CortexMaterial/
│       │   ├── CortexEditor/
│       │   ├── CortexLevel/
│       │   ├── CortexUMG/
│       │   ├── CortexReflect/
│       │   └── CortexQA/
│       └── MCP/
│           ├── src/cortex_mcp/
│           ├── tools/{domain}/
│           └── tests/            ← MCP benchmark tests (E2E, scenarios, stress)
├── Saved/
│   ├── CortexPort.txt          ← TCP port (auto-generated)
│   └── Logs/
├── ProjectName.uproject
└── CLAUDE.md                   ← project instructions
```

## Key Files

| File | Purpose |
|------|---------|
| `.cortex/config.yaml` | Engine path, active domains, doc references |
| `.cortex/context.md` | Shared project knowledge for all agents |
| `.mcp.json` | MCP server connection config |
| `Saved/CortexPort.txt` | TCP port for MCP ↔ editor communication |
| `Plugins/UnrealCortex/UnrealCortex.uplugin` | Plugin module list |
| `cortex-toolkit/hooks/check-ue-editor.sh` | PreToolUse guard — auto-verifies/starts editor before MCP calls |
| `cortex-toolkit/hooks/hooks.json` | Hook configuration (PreToolUse + SessionStart) |

## Content Organization Rules

- DataTables go in `Content/Data/` with `DT_` prefix
- Test-generated assets go in `Content/Temp/` (git-ignored)
- Each domain has its own content subdirectory
- GameplayTags stored in `Config/Tags/*.ini`, not in DataTables
