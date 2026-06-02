# Cortex Toolkit

AI-powered Unreal Engine development toolkit. Skills, agents, and domain knowledge for Claude Code, Codex, and Cursor — powered by UnrealCortex MCP.

## Platform Support

| Feature | Claude Code | Codex | Cursor |
|---------|-------------|-------|--------|
| Skills (`skills/`) | ✅ | ✅ via symlink | ✅ |
| Agents (`agents/`) | ✅ | ❌ | ✅ |
| Hooks (`hooks/`) | ✅ | ❌ | ⚠️ |
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

Then open your project and run `/cortex-init` to configure MCP and project memory.

### Codex

See [`.codex/INSTALL.md`](.codex/INSTALL.md) for full instructions.

```bash
git clone https://github.com/etelyatn/cortex-toolkit.git ~/.cortex-toolkit
# Create a symlink in your project root
ln -s ~/.cortex-toolkit/skills skills
```

### Cursor

See [`docs/cursor-setup.md`](docs/cursor-setup.md) for full instructions.

### Manual Setup

If you prefer not to use `/cortex-init`, add the context block manually:

- **Claude Code:** Append [`templates/claude-block.md`](templates/claude-block.md) to your project's `CLAUDE.md`
- **Codex:** Append [`templates/agents-block.md`](templates/agents-block.md) to your project's `AGENTS.md`

Then create `.cortex/` manually following the structure in [Project Memory](#project-memory).

## Getting Started

1. Open your Unreal project in the editor (CortexCore writes a port file on startup)
2. Run `/cortex-start` to verify the connection and get a guided introduction
3. Run `/cortex-help` anytime to discover available skills or get contextual suggestions

## Skills

Skills are invoked with `/skill-name` in Claude Code. Skills launch specialized agents to handle complex workflows and keep your conversation clean by running MCP tool sequences in the background.

### Blueprint

| Skill | Description |
|-------|-------------|
| `/cortex-blueprint` | Create, modify, review, or debug Blueprints — structure, graphs, variables, functions, best practices |
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

### QA

| Skill | Description |
|-------|-------------|
| `/cortex-qa-init` | Prepare QA context and generate an initial game profile for scenario-driven testing |
| `/cortex-qa-interactive` | Drive live exploratory testing in PIE with tight observe-act-assert loops |
| `/cortex-qa-run` | Execute a scenario file through the QA agent and return findings with report artifacts |

### Reflect

| Skill | Description |
|-------|-------------|
| `/cortex-reflect` | Assess blast radius before breaking changes, or analyze class architecture and cross-references |

### UI

| Skill | Description |
|-------|-------------|
| `/cortex-ui` | Create or review UMG widgets, screens, or UI components |

### Core

| Skill | Description |
|-------|-------------|
| `/cortex-help` | Discover available skills and get contextual guidance |
| `/cortex-init` | Initialize a new project with Cortex configuration |
| `/cortex-start` | Start a Cortex session, verify editor connection, and run guided onboarding |
| `/cortex-test` | Run Unreal C++ and Python MCP tests (dual-track test runner) |

### Operations

| Skill | Description |
|-------|-------------|
| `/cortex-build` | Build the Unreal project after modifying C++ source files |
| `/cortex-editor` | Open the Unreal Editor when it needs to be running |
| `/cortex-restart` | Restart the Unreal Editor after C++ changes need recompilation |
| `/cortex-schema-refresh` | Refresh `.cortex/schema/` project snapshot files |
| `/cortex-status` | Check MCP connection health, editor status, and connection recovery |

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
├── context.md           # Project-specific conventions (read every session)
├── domains/             # Domain-specific knowledge files
│   ├── blueprints.md
│   ├── data.md
│   ├── level.md
│   ├── material.md
│   ├── statetree.md
│   ├── qa.md
│   └── umg.md
└── schema/              # LLM-readable project snapshots
    ├── _catalog.md      # Index of all schema files
    └── ...
```

Fill the domain files with your project's specifics. Agents use this context to work without repeated questions. Run `/cortex-schema-refresh` to regenerate schema snapshots from live editor data.

## Migration from v0.1.x

If you were using the old multi-plugin structure (8 separate plugins like `cortex-core`, `cortex-data`, etc.):

1. Uninstall all individual domain plugins: `claude plugin uninstall cortex-core` (repeat for each)
2. Add the marketplace and install the unified plugin: `claude plugin marketplace add etelyatn/cortex-toolkit && claude plugin install cortex-toolkit`
3. Update any custom `subagent_type` references from `cortex-{domain}:agent-name` to `cortex-toolkit:agent-name`

## Development

This toolkit was restructured from 8 separate plugins into a single unified plugin. For architecture decisions and rationale, see the [design doc](https://github.com/etelyatn/CortexSandbox/blob/main/docs/plans/2026-03-01-cortex-toolkit-unified-design.md).

## License

MIT
