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

### OpenCode

Tell OpenCode:

```
Fetch and follow instructions from https://raw.githubusercontent.com/etelyatn/cortex-toolkit/main/.opencode/INSTALL.md
```

This installs the toolkit as a plugin from git and registers the `cortex-*` skills. The INSTALL.md
quick start then walks you through `cortex-setup` (project setup and onboarding), `cortex-editor`
(editor connection), and the domain skills. Full details: [`.opencode/INSTALL.md`](.opencode/INSTALL.md).

### Manual Setup

If you prefer not to use `/cortex-setup`, add the context block manually:

- **Claude Code:** Append [`templates/context-block.md`](templates/context-block.md) to your project's `CLAUDE.md`
- **Codex:** Append [`templates/context-block.md`](templates/context-block.md) to your project's `AGENTS.md`

Then create `.cortex/` manually following the structure in [Project Memory](#project-memory). Codex users can also install the packaged plugin and keep the same AGENTS.md context block for project-specific rules.

## Getting Started

1. Start with `/cortex-setup` (or `cortex-setup` in Codex) for onboarding, initialization, schema refresh, and next-step guidance.
2. Use `/cortex-editor` for editor lifecycle, MCP diagnostics, and explicit restarts.
3. Use `/cortex-build` only for compile/build requests.

## Skills

Skills are invoked with `/skill-name` in Claude Code. Each skill runs a focused workflow and keeps your conversation clean by running MCP tool sequences.

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
| `/cortex-animation` | Inspect skeletal animation assets and author guarded named notifies, curves, sections, sockets, object notifies, and notify states through capability-gated `anim_cmd` commands |

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
│   ├── qa.md
│   ├── umg.md
│   └── anim.md
└── schema/              # LLM-readable project snapshots
    ├── _catalog.md      # Index of all schema files
    └── ...
```

Check `.cortex/config.yaml` into version control for shared defaults. Put machine-specific values such as a local Unreal Engine source-build path in `.cortex/config.local.yaml`; toolkit loaders merge it over the shared config when present.

`config.local.yaml` uses the same shape as `config.yaml`. Dictionaries merge recursively, while lists and scalar values replace the shared value. Keep `config.local.yaml` out of version control; use it for fields that differ per workstation, especially `engine.path`. If no effective `engine.path` is configured, editor helpers fall back to `UE_PATH`.

Fill the domain files with your project's specifics. The AI uses this context to work without repeated questions. Run `/cortex-setup` and ask it to refresh the schema to regenerate snapshots from live editor data.

## Migration from v0.1.x

If you were using the old multi-plugin structure (8 separate plugins like `cortex-core`, `cortex-data`, etc.):

1. Uninstall all individual domain plugins: `claude plugin uninstall cortex-core` (repeat for each)
2. Add the marketplace and install the unified plugin: `claude plugin marketplace add etelyatn/cortex-toolkit && claude plugin install cortex-toolkit`

## Development

This toolkit was restructured from 8 separate plugins into a single unified plugin. For architecture decisions and rationale, see the [design doc](https://github.com/etelyatn/CortexSandbox/blob/main/docs/plans/2026-03-01-cortex-toolkit-unified-design.md).

## License

MIT
