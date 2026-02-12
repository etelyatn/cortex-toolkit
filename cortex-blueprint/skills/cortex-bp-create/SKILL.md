---
name: cortex-bp-create
description: Use when creating new Blueprints with variables, functions, or components from a spec or description
---

# Blueprint Create

Creates Blueprint assets with structure from specifications.

## Before Starting

Read `.cortex/domains/blueprints.md` for project conventions and existing class hierarchy.

## Steps

### 1. Understand the Spec

Determine from the user's description:
- Blueprint type (Actor, ActorComponent, FunctionLibrary, Interface, custom parent)
- Name (following project conventions)
- Variables (name, type, default, category, exposed)
- Functions (name, inputs, outputs)
- Components (for Actor BPs)

### 2. Choose Parent Class

Use `list_blueprints` and project conventions to pick the right parent:
- Gameplay entity → `AActor` or project-specific base class
- Reusable behavior → `UActorComponent`
- Static utility functions → `UBlueprintFunctionLibrary`
- Shared interface → `UInterface`

### 3. Create Blueprint

```
create_blueprint(name, path, parent_class)
```

Path should follow project structure (e.g., `/Game/Blueprints/`).

### 4. Add Variables

For each variable in the spec:
```
add_blueprint_variable(blueprint_path, variable_name, variable_type, options)
```

Options: `default_value`, `is_exposed`, `category`

### 5. Add Functions

For each function in the spec:
```
add_blueprint_function(blueprint_path, function_name, options)
```

Note: Function implementation (node graphs) requires manual work in the editor.

### 6. Compile and Save

```
compile_blueprint(blueprint_path) → save_blueprint(blueprint_path)
```

Verify compilation succeeds. If not, check variable types and function signatures.

### 7. Verify

Use `get_blueprint_info` to confirm the Blueprint matches the spec:
- Correct parent class
- All variables present with right types
- All functions created
- Compilation status clean
