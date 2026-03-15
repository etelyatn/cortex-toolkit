# Blueprint Domain Context
> Fill in the sections below. Delete the HTML comment examples as you go.
> Agents read this file before every task.

## Class Hierarchy

<!-- List your key Blueprint classes and their parents.
     WHY: The agent uses this to resolve parent class names when creating or modifying Blueprints,
     and to understand inheritance relationships before touching shared base classes.
     Example:
     - YourBP_BasePickup (Actor) — base for all pickups; do not add game logic here
     - YourBP_BaseEnemy (Character) — base for all enemies; health/movement in C++
     - YourBPC_HealthSystem (ActorComponent) — shared health logic; used by Player and Enemy
-->

## Conventions

<!-- Blueprint naming and organization rules.
     WHY: The agent follows these when creating new assets or renaming existing ones.
     Example:
     - Actors: BP_{Category}_{Name} (e.g. BP_Pickup_YourItem)
     - Components: BPC_{Name} (e.g. BPC_YourInventory)
     - Interfaces: BPI_{Name} (e.g. BPI_YourInteractable)
     - All gameplay BPs in Content/Blueprints/{Category}/
-->

## Key Blueprints

<!-- List the most important BPs that agents should know about.
     WHY: The agent checks here first when a task involves a named Blueprint — this prevents
     searching the asset registry unnecessarily and avoids touching the wrong file.
     Example:
     - YourBP_PlayerCharacter — main player pawn; depends on YourBPC_InventoryManager
     - YourBP_GameMode — sets default pawn class and game rules
     - YourBPFL_SharedUtils — static helpers used by most gameplay BPs
-->

## Graph Patterns

<!-- Describe how your Blueprints wire together at a high level.
     WHY: Before modifying graphs the agent must understand which event patterns are in use,
     how BPs communicate via interfaces, and which common nodes are expected in each graph.
     Without this context the agent may add redundant event bindings or break interface calls.
-->

### Interface Usage

<!-- List interfaces your BPs implement and how they are called.
     Example:
     - YourBPI_Interactable — implemented by YourBP_Door, YourBP_Chest, YourBP_Switch
       Called from YourBP_PlayerCharacter via "Does Implement Interface" + interface message node
     - YourBPI_Damageable — implemented by all enemy BPs
       Called from YourBPFL_CombatUtils.ApplyDamage static function
-->

### Common Event Patterns

<!-- List the event entry points that most of your gameplay BPs rely on.
     WHY: The agent must know which events are already present before adding new ones —
     duplicate event nodes cause compile errors.
     Example:
     - BeginPlay — used for initialization: spawn components, bind delegates, load save data
     - Tick — enabled only on YourBP_BaseEnemy and YourBP_Projectile; disabled elsewhere for performance
     - Component events — YourBPC_HealthSystem broadcasts OnDeath delegate; subscribers bind in BeginPlay
     - Custom events — prefer named Custom Events over functions when called from timers or async nodes
-->

### Typical Graph Structure

<!-- Describe the expected shape of graphs in your project so the agent adds nodes consistently.
     Example:
     - EventGraph: entry via BeginPlay or input events only; heavy logic delegated to functions
     - Functions: pure functions for queries (no side effects); impure for state changes
     - Macros: avoid — use function libraries (YourBPFL_*) for shared logic instead
     - Max node count per graph: 30 before splitting into sub-functions (project rule)
-->
