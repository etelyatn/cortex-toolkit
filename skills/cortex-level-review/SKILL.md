---
name: cortex-level-review
description: Use when reviewing level content, auditing actor organization, checking scene structure, or analyzing spatial layout
---

# Level Review

Reviews level content and organization using the Level Designer agent.

## Steps

### 1. Launch Level Designer Agent

<!-- Turn budget: REVIEW tier (max_turns=15) — read + analyze + report pattern -->
Use the Task tool with `subagent_type: "cortex-toolkit:level-designer"` and `max_turns: 15` to delegate the review.

Pass context about what to review:

```
Review the current level and provide a report:

1. Use `get_info` for level overview (name, actor count, world type, sublevels)
2. Use `list_actors` to enumerate actors (paginate if needed)
3. Use `get_bounds` to understand spatial layout
4. Check folder organization -- are actors organized logically?
5. Check for common issues:
   - Actors without folders
   - Duplicate labels
   - Actors at origin that shouldn't be
   - Unloaded sublevels
6. Summarize findings with recommendations
```

### 2. Agent Workflow (runs in background)

The Level Designer agent will:
1. Query level info and actor lists
2. Analyze organization patterns
3. Check spatial distribution
4. Report findings and recommendations

### 3. Review Agent Results

The agent returns:
- Level overview (name, actor count, world type)
- Actor breakdown by class and folder
- Spatial bounds information
- Organization issues found
- Recommendations for improvement

## Handling Agent Results

If the agent's response includes a **Status** line:
- **completed** — present the findings to the user as-is.
- **blocked** / **partial** — surface what was done, what remains, and what blocked it. Let the user decide whether to re-invoke for the remaining scope.

If the agent's response has no Status line (e.g., turn limit reached mid-response), treat as **partial** — summarize whatever the agent produced and note that the review may be incomplete.
