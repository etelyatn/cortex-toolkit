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

## Getting Started

1. Open your Unreal project in the editor (CortexCore writes a port file on startup)
2. Run `/cortex-start` to verify the connection and get a guided introduction
3. Run `/cortex-help` anytime to discover available skills or get contextual suggestions

## Skills

Skills are invoked with `/skill-name` in Claude Code. Skills launch specialized agents to handle complex workflows and keep your conversation clean by running MCP tool sequences in the background.

### Blueprint

| Skill | Description |
|-------|-------------|
| `/cortex-bp-create` | Create Blueprint assets, add variables, and implement functions |
| `/cortex-bp-review` | Review Blueprint graph for structure, naming, complexity, and UE best practices |
| `/cortex-bp-migrate` | Migrate Blueprints to C++ using the V7 migration pipeline |

### Data

| Skill | Description |
|-------|-------------|
| `/cortex-data-create` | Create and populate DataTables, DataAssets, and related data assets from specs |
| `/cortex-data-review` | Review DataTables, DataAssets, and data for quality and balance issues |

### Level

| Skill | Description |
|-------|-------------|
| `/cortex-level-edit` | Edit level actors, transforms, and organization using the batch-first methodology |
| `/cortex-level-review` | Review level content and organization |

### Material

| Skill | Description |
|-------|-------------|
| `/cortex-material-create` | Create materials, instances, and parameter collections from specifications |
| `/cortex-material-review` | Review materials, instances, and parameter collections for structure and performance |

### QA

| Skill | Description |
|-------|-------------|
| `/cortex-qa-init` | Prepare QA context and generate an initial game profile for scenario-driven testing |
| `/cortex-qa-interactive` | Drive live exploratory testing in PIE with tight observe-act-assert loops |
| `/cortex-qa-run` | Execute a scenario file through the QA agent and return findings with report artifacts |

### Reflect

| Skill | Description |
|-------|-------------|
| `/cortex-impact` | Analyze cross-system impact of changes before making them |
| `/cortex-reflect` | Analyze project class architecture and cross-references |

### UI

| Skill | Description |
|-------|-------------|
| `/cortex-ui-create` | Create UMG widget screens using the composite widget creation tool |
| `/cortex-ui-review` | Review UMG widget hierarchies for structure, layout patterns, and best practices |

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
| `/cortex-reconnect` | Reconnect to the Cortex MCP server when connection is lost |
| `/cortex-restart` | Restart the Unreal Editor after C++ changes need recompilation |
| `/cortex-schema-refresh` | Refresh `.cortex/schema/` project snapshot files |
| `/cortex-status` | Check MCP connection health and editor status |

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
| `data-architect` | Data | Design and build data structures, schemas, and GameplayTag hierarchies |
| `data-balancer` | Data | Analyze and balance game data, tune DataTables, validate progression curves |
| `level-designer` | Level | Design and edit levels, spawn actors, manage transforms and organization |
| `material-developer` | Material | Create and modify materials, expression graphs, and parameter collections |
| `project-analyzer` | Reflect | Analyze project architecture, class hierarchies, and cross-class symbol references |
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
│   ├── core.md
│   ├── data.md
│   └── ...
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
