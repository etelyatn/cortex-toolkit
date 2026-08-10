# Cortex Toolkit — Cursor Setup

## Installation

1. Open Cursor settings → Extensions → Install from directory
2. Point to your local clone of cortex-toolkit (or the submodule path in your project)

## What Works

| Feature | Supported |
|---------|-----------|
| Skills (`skills/`) | ✅ |
| Hooks (`hooks/`) | ⚠️ Depends on Cursor version |

## Getting Started

Open your Unreal project in Cursor, then use the skill `/cortex-setup` to begin.

## Troubleshooting

- **Hooks not firing:** Check your Cursor version — hook support may not be available in all versions.
- **MCP not connecting:** Verify `.mcp.json` is configured and the Unreal Editor is running.
