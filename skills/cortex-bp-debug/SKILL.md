---
name: cortex-bp-debug
description: Use when tracing Blueprint execution, finding graph function calls, or diagnosing unexpected Blueprint behavior with graph_search_nodes and connected_to.
---

I'm using the cortex-bp-debug skill to investigate Blueprint graph flow.

Read `.cortex/domains/blueprints.md` for available tools and patterns before starting.

Then use the Agent tool to launch `cortex-toolkit:blueprint-debugger` with:
- The Blueprint asset path
- The investigation goal (execution trace / find function / explain behavior)
- Any specific node or behavior to start from
