# UE Project Structure

Standard layout for UnrealCortex-powered projects.

## Directory Layout

```
ProjectRoot/
├── .cortex/                    ← project memory (AI context)
│   ├── config.yaml
│   ├── config.local.yaml        ← optional per-machine overrides (git-ignored)
│   ├── context.md
│   └── domains/
├── .mcp.json                   ← MCP server configuration
├── Config/                     ← UE config files
│   └── Tags/                   ← GameplayTag .ini files
├── Content/                    ← UE assets
│   ├── AI/                      ← AI-facing content
│   │   └── StateTrees/          ← StateTree assets
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
│       │   ├── CortexQA/
│       │   └── CortexStateTree/
│       └── MCP/
│           ├── src/cortex_mcp/
│           ├── tools/{domain}/
│           └── tests/            ← MCP benchmark tests (E2E, scenarios, stress)
├── Saved/
│   ├── CortexPort-{PID}.txt    ← TCP port (auto-generated, per editor instance)
│   └── Logs/
├── ProjectName.uproject
└── CLAUDE.md                   ← project instructions
```

## Key Files

| File | Purpose |
|------|---------|
| `.cortex/config.yaml` | Shared engine defaults, active domains, doc references |
| `.cortex/config.local.yaml` | Optional per-machine overrides merged over shared config |
| `.cortex/context.md` | Shared project knowledge for all agents |
| `.mcp.json` | MCP server connection config |
| `Saved/CortexPort-{PID}.txt` | TCP port for MCP ↔ editor communication (one per editor instance) |
| `Plugins/UnrealCortex/UnrealCortex.uplugin` | Plugin module list |
| `cortex-toolkit/hooks/check-ue-editor.sh` | PreToolUse guard — auto-verifies/starts editor before MCP calls |
| `cortex-toolkit/hooks/hooks.json` | Hook configuration (PreToolUse + SessionStart) |

## Content Organization Rules

- DataTables go in `Content/Data/` with `DT_` prefix
- Test-generated assets go in `Content/Temp/` (git-ignored)
- Each domain has its own content subdirectory
- StateTree assets should live in `Content/AI/StateTrees/` or `Content/StateTrees/` with `ST_` prefix
- GameplayTags stored in `Config/Tags/*.ini`, not in DataTables
