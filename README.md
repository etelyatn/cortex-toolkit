# Cortex Toolkit

AI-powered Unreal Engine development toolkit. Skills and domain knowledge for Claude Code, Codex, Cursor, and OpenCode — powered by UnrealCortex MCP.

## Platform Support

| Feature | Claude Code | Codex | Cursor | OpenCode |
|---------|-------------|-------|--------|----------|
| Skills (`skills/`) | ✅ | ✅ via Codex plugin | ✅ | ✅ via plugin |
| Hooks (`hooks/`) | ✅ | ✅ requires trust | ⚠️ | ✅ via plugin |
| MCP tools | ✅ | ✅ | ✅ | ✅ |

## Prerequisites

- **Unreal Engine 5.6+** with [UnrealCortex](https://github.com/etelyatn/UnrealCortex) plugin installed
- **Python 3.10+** with [uv](https://docs.astral.sh/uv/) (for the MCP server)
- **Claude Code**, **Codex**, **Cursor**, or **OpenCode**

## Installation

### Claude Code

```bash
claude plugin marketplace add etelyatn/cortex-toolkit
claude plugin install cortex-toolkit
```

Then open your project and run `/cortex-start`. It will verify the editor/MCP connection and guide you through setup. If you only need the project configuration step, run `/cortex-init` directly.

### Codex

See [`.codex/INSTALL.md`](.codex/INSTALL.md) for full instructions.

```bash
codex plugin marketplace add etelyatn/cortex-toolkit
codex plugin add cortex-toolkit@cortex-toolkit
```

Then restart Codex if it was already running.
Your Unreal project still needs a project-local `.mcp.json` pointing to the UnrealCortex MCP server.
Codex discovers the toolkit hooks automatically and asks you to trust them before they run.
Start with `cortex-start` for guided onboarding, or use `cortex-init` directly when you only want MCP and `.cortex/` setup.

### Cursor

See [`docs/cursor-setup.md`](docs/cursor-setup.md) for full instructions.

### OpenCode

Tell OpenCode:

```
Fetch and follow instructions from https://raw.githubusercontent.com/etelyatn/cortex-toolkit/main/.opencode/INSTALL.md
```

OpenCode fetches the instructions, installs the toolkit as a plugin from git, and registers the
`cortex-*` skills. Then run `cortex-init` in your project to configure MCP and `.cortex/`.
Full details: [`.opencode/INSTALL.md`](.opencode/INSTALL.md).

### Manual Setup

If you prefer not to use `/cortex-init`, add the context block manually:

- **Claude Code:** Append [`templates/context-block.md`](templates/context-block.md) to your project's `CLAUDE.md`
- **Codex:** Append [`templates/context-block.md`](templates/context-block.md) to your project's `AGENTS.md`

Then create `.cortex/` manually following the structure in [Project Memory](#project-memory). Codex users can also install the packaged plugin and keep the same AGENTS.md context block for project-specific rules.

## Getting Started

1. Start with `/cortex-start` (or `cortex-start` in Codex) for guided onboarding, editor/MCP verification, and next-step recommendations.
2. If you want only setup without the full guided flow, run `/cortex-init` or `cortex-init` to configure MCP and `.cortex/` project memory.
3. After init or structural content changes, run `/cortex-schema-refresh` or `cortex-schema-refresh` so `.cortex/schema/` contains current project data.
4. Run `/cortex-help` anytime to discover available skills or get contextual suggestions.

## Skills

Skills are invoked with `/skill-name` in Claude Code. Each skill runs a focused workflow and keeps your conversation clean by running MCP tool sequences.

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
| `/cortex-qa-run` | Execute a predefined gameplay QA scenario and collect findings |

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

## Project MemoryCortex Toolkit reads project-specific knowledge from `.cortex/`:

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
│   ├── qa.md
│   └── umg.md
└── schema/              # LLM-readable project snapshots
    ├── _catalog.md      # Index of all schema files
    └── ...
```

Check `.cortex/config.yaml` into version control for shared defaults. Put machine-specific values such as a local Unreal Engine source-build path in `.cortex/config.local.yaml`; toolkit loaders merge it over the shared config when present.

`config.local.yaml` uses the same shape as `config.yaml`. Dictionaries merge recursively, while lists and scalar values replace the shared value. Keep `config.local.yaml` out of version control; use it for fields that differ per workstation, especially `engine.path`. If no effective `engine.path` is configured, editor helpers fall back to `UE_PATH`.

Fill the domain files with your project's specifics. The AI uses this context to work without repeated questions. Run `/cortex-schema-refresh` to regenerate schema snapshots from live editor data.

## Migration from v0.1.x

If you were using the old multi-plugin structure (8 separate plugins like `cortex-core`, `cortex-data`, etc.):

1. Uninstall all individual domain plugins: `claude plugin uninstall cortex-core` (repeat for each)
2. Add the marketplace and install the unified plugin: `claude plugin marketplace add etelyatn/cortex-toolkit && claude plugin install cortex-toolkit`

## Development

This toolkit was restructured from 8 separate plugins into a single unified plugin. For architecture decisions and rationale, see the [design doc](https://github.com/etelyatn/CortexSandbox/blob/main/docs/plans/2026-03-01-cortex-toolkit-unified-design.md).

## License

MIT
