---
name: cortex-bp-review
description: Use when reviewing Blueprint structure, complexity, naming conventions, or best practices compliance
---

# Blueprint Review

Reviews Blueprint assets for structure, naming, complexity, and UE best practices.

## Before Starting

Read `.cortex/domains/blueprints.md` for project-specific BP conventions and class hierarchy.

## Steps

### 1. List Blueprints

Use `list_blueprints` to get all Blueprint assets, optionally filtered by path.

### 2. Inspect Each Blueprint

For each Blueprint under review:
- `get_blueprint_info` — check type, parent class, compilation status, variable/function count
- `graph_list_graphs` — check graph count and complexity

### 3. Check Structure

**Naming:**
- Verify naming follows project conventions from `.cortex/domains/blueprints.md`
- Default pattern: `BP_{Type}_{Name}` for actors, `BPC_{Name}` for components

**Type appropriateness:**
- Is it the right BP type? (Actor vs ActorComponent vs FunctionLibrary vs Interface)
- Does the parent class make sense?

**Complexity:**
- Count nodes per graph via `graph_list_nodes`
- Flag graphs with >50 nodes — consider splitting into functions
- Flag Blueprints with >10 variables — consider grouping or struct

**Compilation:**
- Is `is_compiled` true? If false, suggest `compile_blueprint`

### 4. Check Variables

- List variables via `get_blueprint_info`
- Verify categories are assigned
- Check for exposed variables that shouldn't be (or vice versa)
- Flag variables without meaningful names

### 5. Report

Group findings by Blueprint:
- **Errors:** Won't compile, broken references
- **Warnings:** Naming violations, high complexity, missing categories
- **Info:** Optimization suggestions, C++ migration candidates
