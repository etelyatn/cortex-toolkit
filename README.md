# Cortex Toolkit

Skills, agents, and domain knowledge for AI coding assistants working with Unreal Engine projects powered by [UnrealCortex](https://github.com/etelyatn/UnrealCortex).

## Plugins

Install only what you need:

| Plugin | Domain | Skills | Agents |
|--------|--------|--------|--------|
| **cortex-core** | Foundation | cortex-init, cortex-build, cortex-test, cortex-status, cortex-editor | Game Architect, Game Designer, Blueprint Debugger, Test Debugger, Project Setup |
| **cortex-data** | DataTables, DataAssets, CurveTables, GameplayTags | cortex-data-review, cortex-data-create | Game Balancer, Data Architect |
| **cortex-blueprint** | Blueprints, Graphs | cortex-bp-review, cortex-bp-create | Blueprint Developer, C++ Migration Specialist |
| **cortex-ui** | UMG Widgets | cortex-ui-review, cortex-ui-create | UI Developer |

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
```

### Claude Code (Direct)

```bash
# Or install directly without marketplace:
claude plugin add etelyatn/cortex-toolkit/cortex-core      # Required
claude plugin add etelyatn/cortex-toolkit/cortex-data       # Pick your domains
claude plugin add etelyatn/cortex-toolkit/cortex-blueprint
claude plugin add etelyatn/cortex-toolkit/cortex-ui
```

### After Installation

```
/cortex-init
```

This sets up `.cortex/` project memory, configures MCP, and detects your Unreal Engine installation.

## Project Memory

The `.cortex/` directory stores project-specific knowledge that agents read automatically:

```
.cortex/
├── config.yaml          ← engine path, active domains
├── context.md           ← shared project knowledge (read every session)
└── domains/
    ├── data.md          ← table schemas, balance rules
    ├── blueprints.md    ← class hierarchy, conventions
    └── umg.md           ← screen inventory, style guide
```

Fill these files with your game's specifics. Agents use this context to work without repeated questions.

## Requirements

- [UnrealCortex](https://github.com/etelyatn/UnrealCortex) plugin installed in your UE project
- Unreal Engine 5.x
- Python 3.10+ with `uv` (for MCP server)

## License

MIT
