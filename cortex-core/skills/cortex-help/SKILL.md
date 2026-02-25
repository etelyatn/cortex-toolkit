---
name: cortex-help
description: Use when the user asks for help, wants to discover available commands, is unsure what to do next, or says "what can I do?" or "what should I do next?"
---

# Cortex Help

Discoverability and contextual guidance for the Cortex Toolkit.

## Argument Parsing

Check the arguments passed to this skill:
- No arguments → **Advisor Mode** (default)
- `all` → **Catalog Mode**
- `agents` → **Agent Catalog Mode**
- Domain keyword → **Domain Mode** (see domain mapping below)
- Unrecognized argument → Fall back to **Advisor Mode** and mention: "No domain called '{arg}'. Run /cortex-help all to see all commands."

**Domain mapping (accept aliases):**

| Argument | Domain |
|----------|--------|
| `data` | data |
| `blueprint`, `bp` | blueprint |
| `material`, `mat` | material |
| `ui`, `umg` | ui |
| `level` | level |
| `qa`, `test` | qa |
| `setup`, `infra` | setup |

---

## Advisor Mode (no arguments)

Gather these signals via file reads only — no MCP calls:

### Signal Gathering

1. **Project initialized?** Check if `.cortex/config.yaml` exists
2. **Editor running?** Check if `Saved/CortexPort.txt` exists. If yes, read the port number.
3. **Schema freshness?** Check if `.cortex/schema/` exists. If yes, check modification time of files inside it.
4. **Content inventory?** Check which `Content/` subdirectories exist:
   - `Content/Data/` → count `.uasset` files
   - `Content/Blueprints/` → count `.uasset` files
   - `Content/Materials/` → count `.uasset` files
   - `Content/UI/` → count `.uasset` files
   - `Content/Maps/` → note map files
5. **Conversation context?** Review the current conversation for domain keywords or recent task context.

### Signal Priority

Generate 2-3 suggestions in this priority order:

1. **Broken infrastructure** → fix first
   - No `.cortex/config.yaml` → suggest `/cortex-init`
   - No `Saved/CortexPort.txt` → suggest `/cortex-editor`
2. **Missing setup** → suggest setup
   - No `.cortex/schema/` or schema older than 7 days → suggest `/cortex-schema-refresh`
   - Empty `.cortex/context.md` (still has template comments) → suggest filling it in
3. **Active work context** → suggest next step
   - User just created something → suggest the matching review skill
   - User working in a domain → suggest related skills
4. **No context** → suggest exploration
   - Has DataTables → suggest `/cortex-data-review`
   - Has Blueprints → suggest `/cortex-bp-review`
   - Nothing detected → suggest `/cortex-start`

### Output Format

Print exactly this structure (15-30 lines):

```
Cortex Toolkit

Editor: {connected (port XXXX) | not running} | Schema: {age or "not generated"}

Suggested Next Steps

1. {Title} — {Rationale with specific numbers}.
   Run {/skill-command} to {action description}.

2. {Title} — {Rationale}.
   Run {/skill-command} to {action description}.

3. {Title} — {Rationale}.
   Run {/skill-command} to {action description}.

---
All commands: /cortex-help all | Domain help: /cortex-help <domain>
```

**Rules:**
- Never show more than 3 suggestions
- Every suggestion must trace to a detected signal — never fabricate
- Use plain language in suggestions ("data definitions" not "schema"), though "Schema" is acceptable in the status line
- Include specific numbers when available ("12 Blueprints" not "some Blueprints")

---

## Catalog Mode (`all` argument)

Print this complete reference grouped by workflow stage:

```
All Commands

Setup & Infrastructure
  /cortex-init              Initialize project configuration
  /cortex-editor            Open Unreal Editor
  /cortex-build             Build the project
  /cortex-status            Check editor connection and module status
  /cortex-reconnect         Reconnect to editor after restart
  /cortex-restart           Restart the MCP server
  /cortex-schema-refresh    Regenerate project schema from live editor

Create
  /cortex-bp-create         Create Blueprints from description or spec
  /cortex-data-create       Create DataTables, DataAssets, GameplayTags
  /cortex-material-create   Create materials and material instances
  /cortex-ui-create         Create UMG widget screens
  /cortex-level-edit        Place and organize actors in levels

Review & Analyze
  /cortex-bp-review         Blueprint health check and improvement suggestions
  /cortex-data-review       DataTable schema review and validation
  /cortex-material-review   Material graph analysis
  /cortex-ui-review         Widget hierarchy and property review
  /cortex-level-review      Level organization and performance review
  /cortex-reflect           Query C++ and Blueprint class hierarchies

Test & QA
  /cortex-test              Run Unreal or Python tests
  /cortex-qa-init           Set up QA test scenarios
  /cortex-qa-run            Execute automated QA scenarios
  /cortex-qa-interactive    Interactive game testing session

Learn
  /cortex-start             Guided onboarding with a real task
  /cortex-bp-migrate        Migrate Blueprints to C++ with analysis

---
Domain help: /cortex-help <domain> (data, bp, mat, ui, level, qa, setup)
```

No signal gathering needed. Print the catalog and stop.

---

## Domain Mode (domain keyword argument)

### Signal Gathering

For the requested domain, gather:
1. **Content inventory** — count assets in the relevant `Content/` subdirectory
2. **Schema status** — check if domain-specific schema files exist in `.cortex/schema/`
3. **Domain context** — check if `.cortex/domains/{domain}.md` exists

### Domain Definitions

**data:**
- Skills: `/cortex-data-create`, `/cortex-data-review`, `/cortex-reflect`, `/cortex-schema-refresh`
- Content path: `Content/Data/`
- Schema files: `.cortex/schema/datatables.md`, `.cortex/schema/structs.md`, `.cortex/schema/tags.md`
- Domain context: `.cortex/domains/data.md`
- Agents: Data Architect, Game Balancer

**blueprint (bp):**
- Skills: `/cortex-bp-create`, `/cortex-bp-review`, `/cortex-bp-migrate`, `/cortex-reflect`
- Content path: `Content/Blueprints/`
- Schema files: `.cortex/schema/blueprints.md`
- Domain context: `.cortex/domains/blueprints.md`
- Agents: Blueprint Developer, Blueprint Debugger, C++ Migration Specialist

**material (mat):**
- Skills: `/cortex-material-create`, `/cortex-material-review`
- Content path: `Content/Materials/`
- Domain context: `.cortex/domains/material.md`
- Agents: Material Developer

**ui (umg):**
- Skills: `/cortex-ui-create`, `/cortex-ui-review`
- Content path: `Content/UI/`
- Domain context: `.cortex/domains/umg.md`
- Agents: UI Developer

**level:**
- Skills: `/cortex-level-edit`, `/cortex-level-review`
- Content path: `Content/Maps/`
- Domain context: `.cortex/domains/level.md`
- Agents: Level Designer

**qa (test):**
- Skills: `/cortex-qa-init`, `/cortex-qa-run`, `/cortex-qa-interactive`, `/cortex-test`
- Domain context: `.cortex/domains/qa.md`
- Agents: QA Engineer, Test Debugger

**setup (infra):**
- Skills: `/cortex-init`, `/cortex-editor`, `/cortex-build`, `/cortex-status`, `/cortex-reconnect`, `/cortex-restart`, `/cortex-schema-refresh`
- Agents: Project Setup, Project Analyzer
- Note: No content path or schema. "Your Project" section should show infrastructure status instead: config exists/missing, editor connected/not, schema freshness.

### Output Format

```
{Domain Name} Domain

Skills
  {/skill-command}     {description}
  {/skill-command}     {description}

Your Project
  {N} {asset type} in {path}
  Schema: {status}
  Domain context: {exists or missing}

Suggested
  {One contextual suggestion based on detected content}

Related
  The {Agent Name} and {Agent Name} agents assist these commands automatically.
```

---

## Agent Catalog Mode (`agents` argument)

Print all agents grouped by domain:

```
Specialist Agents

These agents run autonomously when skills need complex, multi-step work.
You don't invoke them directly — they're launched automatically.

Core
  Game Architect       — System architecture, module planning, BP vs C++ decisions
  Game Designer        — Game mechanics, progression, balance frameworks
  Blueprint Debugger   — Blueprint graph flow analysis, logic diagnosis
  Test Debugger        — Test failure analysis, error patterns, flaky tests

Blueprint
  Blueprint Developer  — Blueprint creation, modification, graph wiring
  C++ Migration Specialist — Blueprint-to-C++ translation and optimization

Data
  Data Architect       — DataTable creation, schema design, bulk data import
  Game Balancer        — Balance analysis, progression curves, reward scaling

Level
  Level Designer       — Actor placement, level organization, streaming

Material
  Material Developer   — Material creation, graph building, parameter setup

QA
  QA Engineer          — Automated game testing, scenario execution

Reflect
  Project Analyzer     — Class hierarchy analysis, cross-references

UI
  UI Developer         — Widget hierarchy, screen building, UMG properties
```
