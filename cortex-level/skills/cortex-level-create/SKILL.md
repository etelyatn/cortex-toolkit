---
name: cortex-level-create
description: Use when constructing a scene with multiple actors, building a lighting rig, populating a level section, or creating an environment layout
---

# Level Create

Creates multi-actor scenes and level layouts using the Level Designer agent.

## Steps

### 1. Launch Level Designer Agent

Use the Task tool with `subagent_type: "cortex-level:level-designer"` to delegate scene construction.

**IMPORTANT: Structure the prompt as a mandatory pipeline directive.** Do NOT pass a free-form natural language description. Instead, pass a structured prompt that forces the agent to use the composite tool:

```
Create the following scene using the MANDATORY pipeline:

**Scene:** [description, e.g. "outdoor lighting rig with sun, sky, and fill lights"]
**Actors:** [list of actors with classes, positions, and properties]
**Organization:** [attachments, folders, tags]
**Save:** true

MANDATORY WORKFLOW:
1. Read `.cortex/domains/level.md` for level conventions
2. Use `get_info` to check current level state
3. Design the complete scene spec as actors[] and organization{}
4. Call `create_level_scene(actors, organization, save)` as a SINGLE call
5. Review results and report

PROHIBITED: Do NOT call spawn_actor, set_folder, set_tags, set_actor_property, set_component_property, or attach_actor individually. These are ONLY for modifying existing actors. For new scenes, you MUST use create_level_scene exclusively.
```

### 2. Agent Workflow (runs in background)

The Level Designer agent will:
1. Read `.cortex/domains/level.md` for project conventions
2. Check current level state with `get_info`
3. Design the full scene spec (actors, properties, organization)
4. **Call `create_level_scene` once** -- atomic creation of all actors + organization in single batch
5. Report results

### 3. Review Agent Results

The agent returns:
- Spawned actor names and count
- Total batch steps completed
- Timing information
- Any failures with step index and error details

## Troubleshooting

**Agent makes individual spawn_actor calls instead of using composite:**
- The structured prompt above should prevent this. If it still happens, verify the agent prompt has the PROHIBITED section intact.

**"ActorNotFound" in organization step:**
- Attachment references use `$ref` to previous spawn results. If a spawn fails, subsequent attachment steps will also fail.
- The batch uses `stop_on_error: true` so it halts at the first failure.

**"Grouping not supported in World Partition":**
- Group/ungroup operations are not available in WP levels. Use folders and tags for organization instead.
