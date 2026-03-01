# Reflect Patterns

Common patterns and best practices for using CortexReflect tools effectively.

## Starting a Session

Always check cache freshness first:

```python
reflect_cache_status()
# If stale or not cached:
scan_project(root="AActor")  # ~2-5 seconds
```

## Detail Levels

Use the right detail level to minimize tokens:

| Level | Fields returned | Use when |
|-------|----------------|----------|
| `summary` | name, type, parent, module, source_path, blueprint_children_count | Browsing hierarchy, listing classes |
| `properties` | + properties, interfaces, components | Working with variables or struct layout |
| `full` | + functions | Function signatures, override analysis |

```python
# Quick overview — minimal tokens
query_class_detail("AMyCharacter", detail="summary")

# Working with properties
query_class_detail("AMyCharacter", detail="properties")

# Full analysis
query_class_detail("AMyCharacter", detail="full", include_inherited=True)
```

## Common Patterns

### Understand a class hierarchy

```python
query_class_hierarchy("ACharacter", depth=3, include_blueprint=True)
```

Returns flat list with `parent` and `depth` fields — easy to read and reason about.

### Full class context in one call

```python
query_class_context("AMyCharacter", detail="properties")
# Returns: parent summary + self at properties level + children summaries
```

Saves 3 separate calls. Use this as the default for "tell me about class X".

### Before refactoring — check blast radius

For a full risk assessment before breaking changes, use `impact_analysis`:

```python
impact_analysis(
    target_class="AMyCharacter",
    symbol="Health",
    change_type="removed_function"  # removed_function | deleted_class | changed_property
)
# Returns: affected Blueprints grouped by severity (high/medium/low),
# with exact node IDs, reference types, and unscanned count
```

For a quick "is anything using this?" check (no graph scan, instant):

```python
get_referencers(asset_path="/Game/Blueprints/BP_MyCharacter")
# Returns: all assets that reference this one via the Asset Registry
```

For forward dependencies ("what does this asset pull in?"):

```python
get_dependencies(asset_path="/Game/Blueprints/BP_MyCharacter")
# Returns: parent classes, referenced meshes, materials, other Blueprints
```

Use `query_usages` directly only when you need graph-level detail for a specific symbol without the full risk scoring overhead.

### Find what Blueprint children override

```python
query_overrides("AMyCharacter", depth=2)
# Returns: per-child list of overridden functions, events, custom additions
```

### Search for classes by name pattern

```python
# query_class_hierarchy with specific root is preferred
# For pattern search, use search_assets for Blueprint assets
```

## Performance Tips

- Use `max_results` to cap large hierarchies (default 100)
- Use `path_filter` in `query_usages` to scope scans: `path_filter="/Game/Characters/"`
- Use `max_blueprints=20` for quick scans, `50` (default) for thorough coverage
- Hierarchy and detail have 30-minute TTL cache — repeated calls are instant
- Usages have 2-minute TTL — always reflects recent Blueprint changes

## Class Name Formats

CortexReflect accepts three formats:

```python
# Short C++ name (prefix optional)
query_class_detail("ACharacter")
query_class_detail("Character")   # same result

# Full C++ name with prefix
query_class_detail("AMyCharacter")

# Blueprint asset path
query_class_detail("/Game/Blueprints/BP_MyCharacter")
```

## Cache Management

```python
# Check freshness
reflect_cache_status()
# → {"cached": true, "age_seconds": 120, "class_count": 47, "stale": false}

# Full rescan (after adding new C++ classes)
rebuild_graph_cache()

# Targeted rescan with custom root
scan_project(root="UObject")  # Everything
scan_project(root="AActor")   # Actors only (faster, default)
```

## Benchmark Tests

Reflect domain workflows are validated by the benchmark testing framework in `Plugins/UnrealCortex/MCP/tests/`:

| Test File | Coverage |
|-----------|----------|
| `test_reflect_tools.py` | All reflect tools: cache_status, scan_project, query_class_hierarchy, query_class_detail, query_class_context, query_overrides, query_usages, get_dependencies, get_referencers, impact_analysis, rebuild_graph_cache |

Run to validate after modifying Reflect MCP tools or C++ command handlers.
