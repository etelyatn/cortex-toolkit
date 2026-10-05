# Cortex Toolkit — Cursor Setup

## Installation

1. Open Cursor settings → Extensions → Install from directory
2. Point to your local clone of cortex-toolkit (or the submodule path in your project)

## What Works

| Feature | Supported |
|---------|-----------|
| Skills (`skills/`) | ✅ |
| Hooks (`hooks/`) | ⚠️ Depends on Cursor version |

When your Cursor version fires hooks, they are **opt-in and disabled by
default**: the PreToolUse editor guard runs only when `hooks.editor_guard: true`
is set in `.cortex/config.yaml`, and the SessionStart context hook runs only when
`hooks.session_context: true` is set. With no config, hooks do nothing.

## Getting Started

Open your Unreal project in Cursor, then use the skill `/cortex-setup` to begin.

## Troubleshooting

- **Hooks not firing:** Check your Cursor version — hook support may not be available in all versions.
- **MCP not connecting:** Verify `.mcp.json` is configured and the Unreal Editor is running.
