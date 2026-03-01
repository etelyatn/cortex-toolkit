# Cortex Toolkit

AI-powered Unreal Engine development toolkit — skills, agents, and domain knowledge for Claude Code, Codex, and Cursor.

Requires the [UnrealCortex](https://github.com/etelyatn/UnrealCortex) plugin running in your Unreal Engine project.

## Support Matrix

| Feature | Claude Code | Codex | Cursor |
|---------|-------------|-------|--------|
| Skills | ✅ | ✅ | ✅ |
| Agents | ✅ | ⚠️ depends on Codex subagent support | ✅ |
| Commands | ✅ | ❌ | ✅ |
| Hooks | ✅ | ❌ | ⚠️ planned |

## Installation

### Claude Code

```bash
/plugin marketplace add cortex-toolkit
/plugin install cortex-toolkit
```

### Codex

See `.codex/INSTALL.md` in this repository.
Agent-backed workflows in Codex depend on your Codex build supporting `cortex-toolkit:*` subagent types.

### Cursor

Install via `.cursor-plugin/plugin.json` in this repository.

## Getting Started

After installation, run `/cortex-start` for guided onboarding. It checks your setup, verifies the MCP connection to the running Unreal Editor, and walks you through your first task.

Run `/cortex-help` anytime to discover available skills or get contextual suggestions.

## Skills

Skills are slash commands that launch specialized agents to handle complex workflows. They keep your conversation clean by running MCP tool sequences in the background.

### Blueprint

| Skill | Description |
|-------|-------------|
| `/cortex-bp-create` | Use when creating new Blueprints with variables, functions, or components from a spec or description |
| `/cortex-bp-review` | Use when reviewing Blueprint structure, complexity, naming conventions, or best practices compliance |
| `/cortex-bp-migrate` | Migrate Blueprint logic to C++, or audit a Blueprint for migration candidates. Supports `--audit` (analysis only) and `--dry-run` (generate but don't write) |
| `/cortex-bp-migrate-guided` | Interactive Blueprint-to-C++ migration with phase-based agents, scope gates, partial mode, and resume support |

### Data

| Skill | Description |
|-------|-------------|
| `/cortex-data-create` | Use when creating new DataTables, DataAssets, CurveTables, or StringTables from a description, spec, or design document |
| `/cortex-data-review` | Use when reviewing DataTables or DataAssets for balance issues, naming convention violations, structural problems, or data integrity checks |

### Core

| Skill | Description |
|-------|-------------|
| `/cortex-start` | Use when new to the toolkit, asking how to get started, or wanting a guided introduction to AI-assisted Unreal Engine development |
| `/cortex-init` | Use when setting up a new Unreal Engine project for AI-assisted development, when `.cortex/` is missing, or when MCP connection needs configuration |
| `/cortex-help` | Use when asking for help, wanting to discover available commands, or unsure what to do next |
| `/cortex-test` | Use when running automation tests, checking test results, or after code changes that need verification. Accepts optional domain parameter |

### Level

| Skill | Description |
|-------|-------------|
| `/cortex-level-edit` | Use when making any change to level content — placing actors, moving or reorganizing existing actors, adjusting lighting, building multi-actor layouts, or reorganizing scene structure |
| `/cortex-level-review` | Use when reviewing level content, auditing actor organization, checking scene structure, or analyzing spatial layout |

### Material

| Skill | Description |
|-------|-------------|
| `/cortex-material-create` | Use when creating new materials, material instances, parameter collections, or building material graphs from a spec or description |
| `/cortex-material-review` | Use when reviewing material structure, parameter usage, graph complexity, instance hierarchies, or checking material best practices compliance |

### QA

| Skill | Description |
|-------|-------------|
| `/cortex-qa-init` | Use when initializing QA workflows for a project and generating a baseline game QA profile |
| `/cortex-qa-run` | Use when executing a predefined gameplay QA scenario and collecting findings |
| `/cortex-qa-interactive` | Use when running a live, interactive QA session with iterative action and observation |

### Reflect

| Skill | Description |
|-------|-------------|
| `/cortex-reflect` | Analyze project class architecture — inheritance trees, Blueprint overrides, cross-references. Use when you need to understand how C++ and Blueprint classes relate |
| `/cortex-impact` | Assess the impact of removing, renaming, or changing a C++ member or Blueprint asset. Use before any breaking change to understand blast radius |

### UI

| Skill | Description |
|-------|-------------|
| `/cortex-ui-create` | Use when creating new widgets, screens, or UI components from a spec, mockup, or description |
| `/cortex-ui-review` | Use when reviewing widget hierarchy, layout patterns, UI structure, or checking UMG best practices compliance |

## Commands

Commands are lightweight utilities that run directly without launching a subagent.

| Command | Description |
|---------|-------------|
| `/cortex-build` | Use when building the Unreal Engine project, after modifying C++ source files, or when build errors need diagnosis |
| `/cortex-editor` | Use when the Unreal Editor needs to be running, MCP connection fails, or user asks to start or open the editor |
| `/cortex-reconnect` | Use when MCP connection is lost or unresponsive. Attempts to reconnect to the Cortex MCP server automatically |
| `/cortex-restart` | Use when the Unreal Editor needs to be restarted, after C++ changes need recompilation, or when the editor is in a bad state |
| `/cortex-schema-refresh` | Use when refreshing project schema files, when `.cortex/schema/` is missing or stale, or when data structures have changed |
| `/cortex-status` | Use when checking MCP connection health, editor status, diagnosing connectivity issues, or verifying domain registration |

## Agents

Domain specialists with deep knowledge of specific Unreal Engine systems. Agents read `.cortex/domains/*.md` to follow your project conventions automatically.

| Agent | Description |
|-------|-------------|
| `blueprint-debugger` | Analyzing Blueprint graph flow, tracing execution paths, diagnosing logic issues in node graphs, or understanding why a Blueprint behaves unexpectedly |
| `blueprint-developer` | Creating, modifying, or fixing Blueprints — adding variables, functions, components, implementing gameplay logic, or troubleshooting Blueprint issues |
| `bp-migration-planner` | Internal pipeline agent invoked by `cortex-bp-migrate`. Phase 1: Blueprint migration analysis and scope selection |
| `bp-migration-executor` | Internal pipeline agent invoked by `cortex-bp-migrate`. Phases 2–6: C++ generation, integration, verification, swap, and report |
| `cpp-migration-specialist` | Translating Blueprint logic to C++, deciding what should stay in BP vs move to native code, or optimizing performance-critical Blueprint systems |
| `data-architect` | Creating or populating data structures from specs, bulk importing data, designing table schemas, or planning the data layer for a new feature |
| `data-balancer` | Analyzing game data for balance issues, progression curves, reward scaling, or cross-table validation |
| `level-designer` | Making any change to level content — placing objects, moving actors, adjusting lighting, organizing the scene, or building multi-actor layouts |
| `material-developer` | Creating, modifying, or debugging materials, material instances, parameter collections, or material expression graphs |
| `project-analyzer` | Analyzing project-wide class architecture, understanding inheritance trees, finding Blueprint overrides, or mapping cross-references |
| `qa-engineer` | Testing gameplay, running QA scenarios, finding bugs in PIE, or validating game mechanics |
| `test-debugger` | Tests are failing, need to understand error patterns, diagnose flaky tests, or figure out why a test passes locally but fails in automation |
| `ui-developer` | Building UMG widget hierarchies, implementing screens, creating game UI (menus, HUDs, dialogs, popups), or working with widget properties and animations |

## Project Memory

The `.cortex/` directory stores project-specific knowledge that agents read automatically at session start:

```
.cortex/
├── config.yaml          — engine path, active domains
├── context.md           — shared project knowledge (injected every session)
├── domains/
│   ├── data.md          — table schemas, balance rules
│   ├── blueprints.md    — class hierarchy, conventions
│   ├── umg.md           — screen inventory, style guide
│   ├── material.md      — material conventions, instance hierarchies
│   └── level.md         — actor conventions, level structure
└── schema/              — LLM-readable project snapshots (generated by cortex-schema-refresh)
```

Fill the domain files with your game's specifics. Agents use this context to work without repeated questions.

## Requirements

- [UnrealCortex](https://github.com/etelyatn/UnrealCortex) plugin installed in your UE project
- Unreal Engine 5.6+
- Python 3.10+ with `uv` (for the MCP server)

## Migration from v0.x

If you were using the old per-domain plugin structure (cortex-core, cortex-data, cortex-blueprint, etc.):

1. Uninstall all individual plugins:
   ```bash
   /plugin uninstall cortex-core
   /plugin uninstall cortex-data
   /plugin uninstall cortex-blueprint
   /plugin uninstall cortex-ui
   /plugin uninstall cortex-material
   /plugin uninstall cortex-level
   /plugin uninstall cortex-qa
   /plugin uninstall cortex-reflect
   ```

2. Install the unified toolkit:
   ```bash
   /plugin install cortex-toolkit
   ```

3. Update any `subagent_type` references in custom prompts or automation — all agents now use the `cortex-toolkit:` namespace (e.g., `cortex-toolkit:blueprint-developer` instead of `cortex-blueprint:blueprint-developer`).

## License

MIT
