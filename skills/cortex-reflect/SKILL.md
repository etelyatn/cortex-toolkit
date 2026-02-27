---
name: cortex-reflect
description: "Analyze project class architecture — inheritance trees, Blueprint overrides, cross-references. Use when you need to understand how C++ and Blueprint classes relate."
---

# CortexReflect — Project Knowledge Graph

Analyze your project's class architecture with a single command.

## Usage

`cortex-reflect AMyCharacter` — Full context for a class
`cortex-reflect hierarchy AMyCharacter` — Inheritance tree
`cortex-reflect usages Health AMyCharacter` — Cross-references

## What it does

1. Checks cache freshness (rebuilds if stale)
2. Queries the class hierarchy, detail, and cross-references
3. Presents a comprehensive summary

## Implementation

Use the project-analyzer agent to execute this skill with the appropriate CortexReflect MCP tools.
