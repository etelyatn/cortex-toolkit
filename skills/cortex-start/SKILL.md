---
name: cortex-start
description: Use when a user is new to the Cortex Toolkit, asks how to get started, runs the toolkit for the first time, or wants a guided introduction to AI-assisted Unreal Engine development
---

# Cortex Start

Guided onboarding for first-time Cortex Toolkit users. Demonstrates value within 60 seconds.

Use skill names directly in instructions (for example `cortex-init`).
**For Claude:** slash aliases are available (for example `/cortex-init`).

## Re-run Detection

Check if `.cortex/onboarded` exists.

- **If exists (returning user):** Ask: "Want the full walkthrough, or just the reference card?"
- **Reference card:** Print Phase 2 reference card, then run Phase 3 (What's Next?).
- **Full walkthrough:** Run all phases (1, 2, 3).
- **If missing (first time):** Run all phases (1, 2, 3) without asking.

---

## Phase 1: Environment Check

Check prerequisites in order. Stop at the first hard failure and guide the user to fix it before continuing.

### 1.1 Project Initialized?

Check if `.cortex/config.yaml` exists.

If missing:
```
Your project hasn't been set up for Cortex yet.
Run `cortex-init` to configure your project — it takes about 30 seconds.
```
Stop here. Do not proceed to 1.2.

### 1.2 Editor Running?

Check if a `Saved/CortexPort-*.txt` port file exists and read the port number.

If missing:
```
The Unreal Editor isn't running (no port file found).
Run `cortex-editor` to open the editor — Cortex needs a live connection.
```
Stop here. Do not proceed to 1.3.

### 1.3 MCP Connected?

Call the `get_status` MCP tool to verify the full connection chain: assistant client -> MCP server -> TCP -> CortexCore.

If the call fails:
```
MCP connection failed — the server can't reach the editor.
Run `cortex-status` to diagnose the issue.
```
Stop here. Do not proceed to 1.4.

If the call succeeds, extract from the response:
- **Project name** — the connected project
- **Engine version** — the UE version
- **Domain count** — number of registered domains
- **Domain list** — names of all registered domains

### 1.4 Report

If some expected domains are missing (compare registered domains against modules in `Plugins/UnrealCortex/UnrealCortex.uplugin`):
```
Note: {N} of {Total} domains registered. Missing: {list}.
These modules may not be enabled in the plugin. Continuing with what's available.
```

If all domains are present, print:
```
All {N} domains connected and ready.
```

Proceed to Phase 2 regardless of missing domains.

---

## Phase 2: Orientation

Print this reference card, substituting `{ProjectName}`, `{Version}`, and `{N}` from the Phase 1 status check:

```
Cortex Toolkit — AI-Assisted Unreal Engine Development

You have 26 skills and 14 specialist agents across 8 domains.

  Quick actions:    cortex-status, cortex-build, cortex-schema-refresh
  Create things:    cortex-bp-create, cortex-data-create, cortex-ui-create
  Review & fix:     cortex-bp-review, cortex-data-review, cortex-level-review
  Testing:          cortex-qa-run, cortex-test
  Need help?        cortex-help

Connected to: {ProjectName} (UE {Version}) — {N} domains active
```

---

## Phase 3: What's Next?

> Applies to all paths: first-time, re-run reference card, and re-run full walkthrough. After Phase 2, always continue here.

Run these steps sequentially to generate prioritized, project-specific suggestions.

### 3.1 Check Reflect Cache (Always First)

Call `reflect_cache_status` first.

If `cached` is false, or `stale` is true, make this suggestion #1:

```
  1. Build the knowledge graph (do this first - everything else improves with it)
     -> "Scan the project and build the Reflect cache"
     Takes ~30-60s. Unlocks class hierarchy, impact analysis, and usage search.
```

If `cached` is true and `stale` is false, skip this suggestion.

### 3.2 Detect Live Project Content

Call:
- `get_data_catalog`
- `list_blueprints` with `path="/Game"`
- `list_blueprints` with `path="/Game"` and `type="Widget"`
- `list_actors` with `limit=1`
- `list_materials` with `path="/Game"`

Record counts from each response. If a call fails, treat that category as 0.

If all TCP-dependent calls fail, print:
```
Lost connection to the editor - run `cortex-status` to diagnose.
```
Skip suggestions.

### 3.2a Check Domain Documentation (Local)

Read `.cortex/domains/*.md`.

A domain file is considered empty if it only contains template text (or has fewer than 10 lines of non-comment content). Track empty files.

### 3.3 Generate Sequenced Suggestions

Build suggestions in dependency order (foundational -> analytical -> creative). Only show content-backed suggestions (except cache scan and ask-anything fallback).

Each suggestion should include:
- sequential number
- short title with live count
- copy-pasteable prompt in quotes
- one-line outcome

Ordering:
1. Reflect cache (if cold/stale)
2. Data domain (if data exists)
3. Blueprints (if blueprints exist)
4. Materials (if materials exist)
5. UMG widgets (if widget blueprints exist)
6. Level content (if actors exist)
7. Domain documentation (if domain docs are empty)
8. Ask-anything fallback

Blank project variant (all counts zero and cache cold):

```
What's next?

  1. Build the knowledge graph
     -> "Scan the project and build the Reflect cache"
     Takes ~30-60s, even for empty projects.

  2. Create your first asset - just describe it:
     -> "Create a Blueprint Actor called BP_MyActor in /Game/Blueprints"

Or just describe what you need - I'll figure out the right tool.
```

### 3.4 Wait for User

After printing suggestions, wait for user input. Do not auto-run a suggestion.

---

## Set Onboarded Flag

After Phase 3 completes, create the file `.cortex/onboarded` with this content:

```
# Cortex onboarding completed
# Date: {current date in YYYY-MM-DD format}
# Re-run cortex-start for the full walkthrough again
```

This prevents the full walkthrough from running automatically on subsequent sessions.
