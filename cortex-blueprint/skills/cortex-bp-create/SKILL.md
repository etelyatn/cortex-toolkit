---
name: cortex-bp-create
description: Use when creating new Blueprints with variables, functions, or components from a spec or description
---

# Blueprint Create

Creates Blueprint assets with structure from specifications using the Blueprint Developer agent.

## Steps

### 1. Launch Blueprint Developer Agent

Use the Task tool with `subagent_type: "cortex-blueprint:blueprint-developer"` to delegate Blueprint creation.

Pass the full user specification including:
- Blueprint type needed (Actor, ActorComponent, FunctionLibrary, Interface, etc.)
- Name and desired path
- Variables (name, type, default value, category, exposed status)
- Functions (name, inputs, outputs)
- Components (for Actor BPs)
- Any specific parent class requirements

### 2. Agent Workflow (runs in background)

The Blueprint Developer agent will:
1. Read `.cortex/domains/blueprints.md` for project conventions
2. Investigate existing Blueprints to choose appropriate parent class
3. Create the Blueprint asset
4. Add all specified variables with proper configuration
5. Add function signatures (implementation requires manual editor work)
6. Compile and save the Blueprint
7. Verify the result matches the specification

All MCP tool calls happen in the background — you won't see each individual call.

### 3. Review Agent Results

The agent returns a summary including:
- Created Blueprint path
- Parent class used
- Variables added
- Functions created
- Compilation status

If the agent encounters issues (compilation errors, invalid types, etc.), it will report them for you to address.

## Why Use the Agent?

- **Clean conversation** — no flood of MCP tool calls
- **Context-aware decisions** — agent reads project conventions and existing patterns
- **Error handling** — agent handles compilation issues and retries
- **Expandable details** — use Ctrl+O to see what the agent did if needed
