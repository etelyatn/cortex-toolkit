---
name: cortex-start
description: Use when a user is new to the Cortex Toolkit, asks how to get started, runs the toolkit for the first time, or wants a guided introduction to AI-assisted Unreal Engine development
---

# Cortex Start

Guided onboarding for first-time Cortex Toolkit users. Demonstrates value within 60 seconds.

## Re-run Detection

Check if `.cortex/onboarded` exists:

- **Exists:** Ask the user: "Want the full walkthrough again, or just the reference card?" If they choose the reference card, skip directly to Phase 2 only. If they want the full walkthrough, run all 4 phases.
- **Missing:** Run all 4 phases in order.

---

## Phase 1: Environment Check

Check prerequisites in order. Stop at the first hard failure and guide the user to fix it before continuing.

### 1.1 Project Initialized?

Check if `.cortex/config.yaml` exists.

If missing:
```
Your project hasn't been set up for Cortex yet.
Run /cortex-init to configure your project — it takes about 30 seconds.
```
Stop here. Do not proceed to 1.2.

### 1.2 Editor Running?

Check if `Saved/CortexPort.txt` exists and read the port number.

If missing:
```
The Unreal Editor isn't running (no port file found).
Run /cortex-editor to open the editor — Cortex needs a live connection.
```
Stop here. Do not proceed to 1.3.

### 1.3 MCP Connected?

Call the `get_status` MCP tool to verify the full connection chain: Claude -> MCP server -> TCP -> CortexCore.

If the call fails:
```
MCP connection failed — the server can't reach the editor.
Run /cortex-status to diagnose the issue.
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

You have 23 skills and 14 specialist agents across 8 domains.

  Quick actions:    /cortex-status, /cortex-build, /cortex-schema-refresh
  Create things:    /cortex-bp-create, /cortex-data-create, /cortex-ui-create
  Review & fix:     /cortex-bp-review, /cortex-data-review, /cortex-level-review
  Testing:          /cortex-qa-run, /cortex-test
  Need help?        /cortex-help

Connected to: {ProjectName} (UE {Version}) — {N} domains active
```

If this was a reference-card-only re-run (from Re-run Detection), stop here. Do not proceed to Phase 3.

---

## Phase 3: Guided First Task

### 3.1 Detect Available Content

Check for existing project content by looking for `.uasset` files (recursively):
- `Content/Data/` — DataTables and data assets
- `Content/Blueprints/` — Blueprint assets

Note the counts for each.

### 3.2 Offer Choices

Based on detected content, present options to the user:

**If DataTables exist:**
```
Your project has {N} DataTables and {M} Blueprints. Want to:

1. Review your DataTables — I'll analyze schemas and suggest improvements
2. Build something new — I'll walk you through creating a Blueprint from a description

Or just start working — run /cortex-help anytime.
```

**If no DataTables but Blueprints exist:**
```
Your project has {M} Blueprints. Want to:

1. Review your Blueprints — I'll check structure, naming, and suggest improvements
2. Build something new — I'll walk you through creating a Blueprint from a description

Or just start working — run /cortex-help anytime.
```

**If no content detected:**
```
Your project is a blank canvas. Want to:

1. Build something new — I'll walk you through creating a Blueprint from a description

Or just start working — run /cortex-help anytime.
```

Wait for the user to choose.

### 3.3 If User Picks "Build Something"

Model what a good prompt looks like by presenting this example:

```
Here's what a great Cortex prompt looks like:

  "Create a Blueprint Actor called BP_Campfire in /Game/Blueprints with a
   PointLight component, a float variable called BurnRate defaulting to 1.0,
   and a bool called bIsLit defaulting to true."

Try it — paste that prompt (or write your own) and I'll build it.
```

Wait for the user to provide a prompt, then execute it using the appropriate skill (typically `/cortex-bp-create`).

### 3.4 Task Completion

After the user completes a task (review or build), proceed to Phase 4.

If the user chooses the escape hatch ("just start working"), skip directly to setting the onboarded flag — do not print the Phase 4 debrief.

---

## Phase 4: Reflection

After the guided task completes, print this debrief:

```
What just happened:
- You described what you wanted in plain language
- A specialist agent handled the multi-step work
- It read your project conventions, created the asset, and compiled

Next steps:
```

Then add contextual next steps — only suggest skills for domains the user actually has content in:

- If Blueprints exist: `  - /cortex-bp-review   — get AI feedback on any Blueprint`
- If DataTables exist: `  - /cortex-data-review  — analyze DataTable schemas and balance`
- If Materials exist: `  - /cortex-material-review — check material graph complexity`
- If UI widgets exist: `  - /cortex-ui-review    — review widget hierarchy and properties`
- If Maps exist: `  - /cortex-level-review — audit level organization and performance`

Always include these two lines at the end:
```
  - /cortex-help        — see all available commands and get suggestions
  - Just describe your next task — no slash command needed for most work
```

---

## Set Onboarded Flag

After Phase 4 completes (or after the user skips with the escape hatch), create the file `.cortex/onboarded` with this content:

```
# Cortex onboarding completed
# Date: {current date in YYYY-MM-DD format}
# Re-run /cortex-start for the full walkthrough again
```

This prevents the full walkthrough from running automatically on subsequent sessions.
