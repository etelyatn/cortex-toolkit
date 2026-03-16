# QA Domain Context
> Fill in the sections below. Delete the HTML comment examples as you go.
> Agents read this file before every task.

## Game Mechanics

<!-- WHY: The QA engineer agent needs to know what systems exist so it can design
     meaningful tests and recognize when something is broken vs. intentional.
     List every testable system — combat, movement, inventory, dialogue, etc.

     Example:
     - Health system: player has 100 HP, regenerates 10/sec after 3s out of combat
     - Inventory: 20-slot grid, items stack up to 99, auto-sort on pickup
     - Door interactions: proximity trigger at 150cm, requires keycard for locked doors
-->

## Controls / Input Mappings

<!-- WHY: The agent injects raw input (key names, axis values) via MCP tools.
     Without this, it cannot map "jump" or "sprint" to actual key bindings.

     Example:
     - Jump: Spacebar
     - Sprint: LeftShift (hold)
     - Interact: E (tap)
     - Attack: LeftMouseButton
     - Aim: RightMouseButton (hold)
     - Pause: Escape
-->

## Test Environment

<!-- WHY: The agent needs a known-good starting state before each test run.
     Describe the default test map, required fixtures, and how to reset state.

     Example:
     - Default test map: /Game/Maps/TestMap
     - Required fixtures: BP_PlayerStart at origin, BP_TestDoor at (500, 0, 0)
     - PIE start conditions: player spawns with full health, empty inventory
     - Reset method: stop + restart PIE (no persistent state between runs)
-->

## Known Issues

<!-- WHY: Prevents the agent from filing duplicate bugs for problems already tracked.
     List known bugs with enough detail to recognize them during testing.

     Example:
     - Door animation stutters on first interaction after PIE start (cosmetic, tracked in JIRA-42)
     - Player can clip through thin walls at high speed (physics, tracked in JIRA-67)
     - Inventory sort crashes if slot count exceeds 20 items (JIRA-89, fix in progress)
-->

## Key Scenarios

<!-- WHY: Tells the agent which test paths matter most and should be prioritized
     in smoke tests or autonomous exploration runs.

     Example:
     - Smoke: spawn player → move to door → interact → verify door opens
     - Smoke: pick up item → open inventory → verify item appears in slot
     - Regression: take 100 damage → verify death state triggers → verify respawn
     - Exploratory: run full clinic level end-to-end, log any assertion failures
-->
