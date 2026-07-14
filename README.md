# Cortex Toolkit

AI-powered Unreal Engine development toolkit. Skills, agents, and domain knowledge for Claude Code, Codex, and Cursor — powered by UnrealCortex MCP.

## Platform Support

| Feature | Claude Code | Codex | Cursor |
|---------|-------------|-------|--------|
| Skills (`skills/`) | ✅ | ✅ via Codex plugin | ✅ |
| Agents (`agents/`) | ✅ | ❌ | ✅ |
| Hooks (`hooks/`) | ✅ | ✅ requires trust | ⚠️ |
| MCP tools | ✅ | ✅ | ✅ |

## Prerequisites

- **Unreal Engine 5.6+** with [UnrealCortex](https://github.com/etelyatn/UnrealCortex) plugin installed
- **Python 3.10+** with [uv](https://docs.astral.sh/uv/) (for the MCP server)
- **Claude Code**, **Codex**, or **Cursor**

## Installation

### Claude Code

```bash
claude plugin marketplace add etelyatn/cortex-toolkit
claude plugin install cortex-toolkit
```

Then open your project and run `/cortex-setup`. It initializes the project when needed, refreshes project memory/schema when requested, and guides you to the next useful action. If editor or MCP lifecycle work is needed, it routes you to `/cortex-editor`.

### Codex

See [`.codex/INSTALL.md`](.codex/INSTALL.md) for full instructions.

```bash
codex plugin marketplace add etelyatn/cortex-toolkit
codex plugin add cortex-toolkit@cortex-toolkit
```

Then restart Codex if it was already running.
Your Unreal project still needs a project-local `.mcp.json` pointing to the UnrealCortex MCP server.
Codex discovers the toolkit hooks automatically and asks you to trust them before they run.
Start with `cortex-setup` for onboarding, initialization, schema refresh, and next-step guidance.

### Cursor

See [`docs/cursor-setup.md`](docs/cursor-setup.md) for full instructions.

### Manual Setup

If you prefer not to use `/cortex-setup`, add the context block manually:

- **Claude Code:** Append [`templates/claude-block.md`](templates/claude-block.md) to your project's `CLAUDE.md`
- **Codex:** Append [`templates/agents-block.md`](templates/agents-block.md) to your project's `AGENTS.md`

Then create `.cortex/` manually following the structure in [Project Memory](#project-memory). Codex users can also install the packaged plugin and keep the same AGENTS.md context block for project-specific rules.

## Getting Started

1. Start with `/cortex-setup` (or `cortex-setup` in Codex) for onboarding, initialization, schema refresh, and next-step guidance.
2. Use `/cortex-editor` for editor lifecycle, MCP diagnostics, and explicit restarts.
3. Use `/cortex-build` only for compile/build requests.

## Skills

Skills are invoked with `/skill-name` in Claude Code. Skills launch specialized agents to handle complex workflows and keep your conversation clean by running MCP tool sequences in the background.

### Blueprint

| Skill | Description |
|-------|-------------|
| `/cortex-blueprint` | Create, modify, review, debug, or reparent Blueprints — structure, graphs, variables, functions, inheritance, and best practices |
| `/cortex-bp-migrate` | Migrate Blueprints to C++ using the V7 migration pipeline |

### Data

| Skill | Description |
|-------|-------------|
| `/cortex-data` | Create, populate, or review DataTables, DataAssets, CurveTables, or StringTables — including balance and integrity checks |

### Level

| Skill | Description |
|-------|-------------|
| `/cortex-level` | Place, organize, or review actors in a level |

### Material

| Skill | Description |
|-------|-------------|
| `/cortex-material` | Create or review materials, instances, parameter collections, or material graphs |

### StateTree

| Skill | Description |
|-------|-------------|
| `/cortex-statetree` | Create, update, review, validate, or compile StateTree assets — structure, hierarchy, tags, and simple transitions |

### Animation

| Skill | Description |
|-------|-------------|
| `/cortex-animation` | Inspect skeletal animation assets and author guarded named notifies, float curves, montage sections, and skeleton sockets through capability-gated `anim_cmd` commands |

### QA

| Skill | Description |
|-------|-------------|
| `/cortex-qa` | Generate QA baselines, run scenario-driven gameplay QA, or start an interactive exploratory QA session |

### Reflect

| Skill | Description |
|-------|-------------|
| `/cortex-reflect` | Assess blast radius before breaking changes, or analyze class architecture and cross-references |

### UMG

| Skill | Description |
|-------|-------------|
| `/cortex-umg` | Create or review UMG widgets, screens, or UI components |

### Core

| Skill | Description |
|-------|-------------|
| `/cortex-setup` | Set up Cortex for a project, get started, refresh schema, or ask what to do next |
| `/cortex-test` | Run Unreal C++ and Python MCP tests (dual-track test runner) |

### Operations

| Skill | Description |
|-------|-------------|
| `/cortex-build` | Build the Unreal project after modifying C++ source files |
| `/cortex-editor` | Start, check, reconnect, or restart the Unreal Editor and MCP connection |

## Agents

Specialized agents launched by skills. Each agent has deep knowledge of a specific Unreal Engine domain and reads `.cortex/domains/*.md` to follow your project conventions automatically.

| Agent | Domain | Description |
|-------|--------|-------------|
| `blueprint-debugger` | Blueprint | Debug Blueprint graph issues and identify root causes |
| `blueprint-developer` | Blueprint | Develop and modify Blueprint assets and graphs |
| `bp-migration-executor` | Blueprint | Execute Blueprint-to-C++ migration tasks |
| `bp-migration-verifier` | Blueprint | Verify migration results for correctness |
| `bp-migration-finalizer` | Blueprint | Finalize migration and clean up source assets |
| `cpp-migration-specialist` | Blueprint | Specialist for analyzing and migrating complex Blueprint logic to C++ |
| `data-architect` | Data | Design and build data structures, schemas, GameplayTags, and StringTable localization migrations |
| `data-balancer` | Data | Analyze and balance game data, tune DataTables, validate progression curves and localized data references |
| `level-designer` | Level | Design and edit levels, spawn actors, manage transforms and organization |
| `material-developer` | Material | Create and modify materials, expression graphs, and parameter collections |
| `project-analyzer` | Reflect | Analyze project architecture, class hierarchies, and cross-class symbol references |
| `statetree-developer` | StateTree | Create, inspect, validate, compile, and modify StateTree structure through UnrealCortex |
| `qa-engineer` | QA | Run and verify game QA scenarios in PIE |
| `test-debugger` | Core | Debug failing Unreal C++ and Python MCP tests |
| `ui-developer` | UI | Develop UMG widget hierarchies, set properties, and create animations |

## Project Memory

Cortex Toolkit reads project-specific knowledge from `.cortex/`:

```
.cortex/
├── config.yaml          # Engine path, active domains, doc references
├── config.local.yaml    # Optional per-machine overrides (git-ignored)
├── context.md           # Project-specific conventions (read every session)
├── domains/             # Domain-specific knowledge files
│   ├── blueprints.md
│   ├── data.md
│   ├── level.md
│   ├── material.md
│   ├── statetree.md
│   ├── anim.md
│   ├── qa.md
│   └── umg.md
└── schema/              # LLM-readable project snapshots
    ├── _catalog.md      # Index of all schema files
    └── ...
```

Check `.cortex/config.yaml` into version control for shared defaults. Put machine-specific values such as a local Unreal Engine source-build path in `.cortex/config.local.yaml`; toolkit loaders merge it over the shared config when present.

`config.local.yaml` uses the same shape as `config.yaml`. Dictionaries merge recursively, while lists and scalar values replace the shared value. Keep `config.local.yaml` out of version control; use it for fields that differ per workstation, especially `engine.path`. If no effective `engine.path` is configured, editor helpers fall back to `UE_PATH`.

Fill the domain files with your project's specifics. Agents use this context to work without repeated questions. Run `/cortex-setup` when you want to refresh schema snapshots from live editor data.

## Migration from v0.1.x

If you were using the old multi-plugin structure (8 separate plugins like `cortex-core`, `cortex-data`, etc.):

1. Uninstall all individual domain plugins: `claude plugin uninstall cortex-core` (repeat for each)
2. Add the marketplace and install the unified plugin: `claude plugin marketplace add etelyatn/cortex-toolkit && claude plugin install cortex-toolkit`
3. Update any custom `subagent_type` references from `cortex-{domain}:agent-name` to `cortex-toolkit:agent-name`

## Development

This toolkit was restructured from 8 separate plugins into a single unified plugin. For architecture decisions and rationale, see the [design doc](https://github.com/etelyatn/CortexSandbox/blob/main/docs/plans/2026-03-01-cortex-toolkit-unified-design.md).

## License

MIT
