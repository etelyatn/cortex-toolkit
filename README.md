# Cortex Toolkit

Skills, agents, and domain knowledge for AI coding assistants working with Unreal Engine projects powered by [UnrealCortex](https://github.com/etelyatn/UnrealCortex).

## Plugins

Install only what you need:

| Plugin | Domain | Skills | Agents |
|--------|--------|--------|--------|
| **cortex-core** | Foundation | cortex-init, cortex-start, cortex-help, cortex-build, cortex-test, cortex-status, cortex-editor, cortex-reconnect, cortex-restart, cortex-schema-refresh | Game Architect, Game Designer, Blueprint Debugger, Test Debugger, Project Setup |
| **cortex-data** | DataTables, DataAssets, CurveTables, GameplayTags | cortex-data-review, cortex-data-create | Game Balancer, Data Architect |
| **cortex-blueprint** | Blueprints, Graphs | cortex-bp-review, cortex-bp-create, cortex-bp-migrate, cortex-bp-migrate-guided | Blueprint Developer, C++ Migration Specialist, BP Migration Guide |
| **cortex-ui** | UMG Widgets | cortex-ui-review, cortex-ui-create | UI Developer |
| **cortex-material** | Materials, Instances, Parameter Collections | cortex-material-review, cortex-material-create | Material Designer |
| **cortex-level** | Actors, Transforms, Components, Queries, Streaming | cortex-level-review, cortex-level-create | Level Designer |
| **cortex-qa** | Gameplay QA, Scenarios, Assertions | cortex-qa-init, cortex-qa-run, cortex-qa-interactive | QA Engineer |
| **cortex-reflect** | C++ & Blueprint class hierarchy, cross-references | cortex-reflect | Project Analyzer |

## Installation

### Claude Code (Marketplace)

```bash
# Add the marketplace
/plugin marketplace add etelyatn/cortex-toolkit

# Then browse and install via /plugins, or install directly:
/plugin install cortex-core@cortex-toolkit      # Required
/plugin install cortex-data@cortex-toolkit       # Pick your domains
/plugin install cortex-blueprint@cortex-toolkit
/plugin install cortex-ui@cortex-toolkit
/plugin install cortex-material@cortex-toolkit
/plugin install cortex-level@cortex-toolkit
/plugin install cortex-qa@cortex-toolkit
/plugin install cortex-reflect@cortex-toolkit
```

### Claude Code (Direct)

```bash
# Or install directly without marketplace:
claude plugin add etelyatn/cortex-toolkit/cortex-core      # Required
claude plugin add etelyatn/cortex-toolkit/cortex-data       # Pick your domains
claude plugin add etelyatn/cortex-toolkit/cortex-blueprint
claude plugin add etelyatn/cortex-toolkit/cortex-ui
claude plugin add etelyatn/cortex-toolkit/cortex-material
claude plugin add etelyatn/cortex-toolkit/cortex-level
claude plugin add etelyatn/cortex-toolkit/cortex-qa
claude plugin add etelyatn/cortex-toolkit/cortex-reflect
```

### After Installation

```
/cortex-start      # Guided onboarding — checks setup, verifies connection, walks you through your first task
```

`/cortex-start` handles everything: if your project isn't configured yet, it guides you through setup first. Then it verifies your editor connection and offers a guided first task to get you productive immediately.

Run `/cortex-help` anytime to discover available commands or get contextual suggestions.

## How It Works

### Skills
Skills are slash commands that launch specialized agents to handle complex workflows. For example:
- `/cortex-material-create` → launches Material Designer agent to build materials/instances from specs
- `/cortex-ui-create` → launches UI Developer agent to build UMG widget hierarchies
- `/cortex-bp-review` → launches Blueprint Developer agent to review graph structure

Skills keep your conversation clean by running MCP tool sequences in the background. Use Ctrl+O to expand agent output if needed.

### Hooks
The `cortex-core` plugin includes hooks that run automatically:
- **PreToolUse guard** — before any MCP tool call, verifies the Unreal Editor is running and CortexCore TCP is responsive. Auto-starts the editor if it's down, with lock-protected parallel safety and a 180s two-phase startup poll.
- **SessionStart** — injects `.cortex/` project memory into the conversation context.

### Agents
Domain specialists with deep knowledge of specific Unreal Engine systems:
- **Material Designer** — creates materials, modifies expression graphs, manages parameter collections
- **UI Developer** — builds UMG hierarchies, sets properties, creates animations
- **Blueprint Developer** — manages Blueprint assets, modifies graphs, analyzes C++ migration
- **BP Migration Guide** — interactive guided migration with level selection, preview, and rollback at each decision gate
- **Game Balancer** — tunes DataTables, validates balance rules, tracks progression curves
- **Data Architect** — designs table schemas, manages GameplayTags, organizes DataAssets
- **Level Designer** — spawns actors, manages transforms, constructs multi-actor scenes, organizes level content
- **Project Analyzer** — queries C++ and Blueprint class hierarchies, finds overrides, tracks cross-class symbol references

Agents read `.cortex/domains/*.md` to follow your project conventions automatically.

### Resources
Each plugin includes pattern documentation and workflow guides:
- `material-patterns.md` — common material graphs (PBR, masked, emissive), instance hierarchies
- `umg-patterns.md` — screen layouts (menu, HUD, dialog), widget naming conventions
- `blueprint-patterns.md` — graph structures, function libraries, event handling
- `level-patterns.md` — actor workflows, scene construction, organization patterns

## Project Memory

The `.cortex/` directory stores project-specific knowledge that agents read automatically:

```
.cortex/
├── config.yaml          ← engine path, active domains
├── context.md           ← shared project knowledge (read every session)
└── domains/
    ├── data.md          ← table schemas, balance rules
    ├── blueprints.md    ← class hierarchy, conventions
    ├── umg.md           ← screen inventory, style guide
    ├── material.md      ← material conventions, instance hierarchies
    └── level.md         ← actor conventions, level structure
```

Fill these files with your game's specifics. Agents use this context to work without repeated questions.

## Known Limitations

These are documented limitations in the current beta:

- **Widget animation keyframing** — Named animations can be created and listed, but property track binding and keyframe creation are not yet available via MCP tools
- **Blueprint compile diagnostics** — `bp.compile` returns success/failure but error details are unstructured text; agents cannot pinpoint specific nodes or graphs causing errors
- **Reflect coverage** — Class hierarchy and usage queries only see Blueprint classes currently loaded in memory; agents should recommend opening relevant Blueprints before scanning
- **Concurrent input sequences** — `run_input_sequence` is designed for single-agent use; multiple agents injecting input simultaneously may produce incorrect results
- **Batch rollback** — If a step in `batch_query` fails, previously completed steps are not rolled back

## Requirements

- [UnrealCortex](https://github.com/etelyatn/UnrealCortex) plugin installed in your UE project
- Unreal Engine 5.6+
- Python 3.10+ with `uv` (for MCP server)

## License

MIT
