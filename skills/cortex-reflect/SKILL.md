---
name: cortex-reflect
description: "Use when assessing blast radius before breaking changes, or analyzing class architecture and cross-references"
---

# CortexReflect — Project Knowledge Graph

Analyze your project's class architecture, or assess the blast radius of a change before making it.

## Usage

`cortex-reflect AMyCharacter` — Full context for a class
`cortex-reflect hierarchy AMyCharacter` — Inheritance tree
`cortex-reflect usages Health AMyCharacter` — Cross-references
`cortex-reflect impact TakeDamage AMyCharacter` — What breaks if I remove this?
`cortex-reflect blast radius /Game/Blueprints/BP_BaseEnemy` — What depends on this asset?

## Execution Paths

### Explore / Understand

**Triggers:** "show hierarchy", "what overrides X", "where is X used", "tell me about class X", general architecture questions

1. Checks cache freshness (rebuilds if stale)
2. Queries the class hierarchy, detail, and cross-references
3. Presents a comprehensive summary

Follow the `resources/project-analysis.md` guide for the analysis workflow.

### Impact / Safety

**Triggers:** "what breaks if", "blast radius", "impact of removing", "is it safe to change", "what depends on"

Execute these steps directly:

#### Step 1. Check Cache Freshness

Call `reflect_cache_status`. If stale (last scan > 30min ago), run `scan_project` first
so class hierarchy + usage scans are current.

#### Step 2. Run Analysis

If symbol + class are provided:
- Call `impact_analysis` with `target_class`, `symbol`, and inferred `change_type`

If only an asset path is provided:
- Call `get_referencers` for a quick package-level dependency list
- For deeper analysis, map asset to class then call `impact_analysis`
  with `change_type="removed_class"`

#### Step 3. Review Results

Present grouped by risk:
1. High risk — compile failures likely
2. Medium risk — runtime behavior likely impacted
3. Low risk — indirect/package-level links

#### Step 4. Handle Partial Coverage

If `not_scanned.count > 0`, ask:

"{N} Blueprints were not scanned (not loaded in editor). Run deep scan for full coverage?"

If user agrees, re-run with `deep_scan=true`.

#### Step 5. Suggest Next Steps

Recommend:
- Which Blueprints to update first (highest risk first)
- Whether the change is safe to proceed
- Safer alternatives when blast radius is too large

### Ambiguous

Default to **Explore / Understand**.

## Handling Results (Explore/Understand path only)

Report results to the user with a completion status:
- **completed** — present the class analysis to the user.
- **blocked** / **partial** — surface what was analyzed and what remains. If the cache was stale or a rebuild was needed, note it.

If the work is interrupted mid-execution, treat it as **partial** — summarize whatever analysis was produced.
