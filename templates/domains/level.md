# Level Domain Context
> Fill in the sections below. Delete the HTML comment examples as you go.
> Agents read this file before every task.

<!-- Level-specific knowledge for level agents. -->

## Level Structure

<!-- WHY: Agents need to know the persistent level name and sublevel layout to target
     the correct level when querying actors or setting sublevel visibility.
     Without this, they may query the wrong level or fail to load required content. -->
<!-- Example:
- Persistent level: YourMainMap
- Sublevels: YourLighting_SL, YourGameplay_SL, YourEnvironment_SL
- World Partition: disabled / enabled (see section below)
-->

## Streaming / World Partition

<!-- WHY: World Partition fundamentally changes how the agent approaches edits.
     In WP levels, actors are loaded by streaming cells — group_actors is not supported,
     sublevels are replaced by data layers, and large levels may have actors outside
     the currently loaded region. The agent must call get_info to check
     is_world_partition before using grouping or sublevel commands. -->
<!-- Example:
- World Partition enabled: yes / no
- Streaming cells: automatic (WP default) / manual cell size YourCellSize
- Data layers: YourDataLayer_Gameplay, YourDataLayer_Lighting, YourDataLayer_Debug
- Traditional sublevels (non-WP only): YourLevel_Lighting, YourLevel_Interior
- Notes: e.g., "WP enabled — use data layers instead of sublevels; group_actors not supported"
-->

## Actor Conventions

<!-- WHY: Consistent naming and folder conventions let the agent find actors predictably
     (e.g., find_actors("Light_*") reliably returns all lights) and place new actors
     in the right folder without asking. -->
<!-- Example:
- Lights in /Lighting folder, prefixed "YourLight_"
- Geometry in /Environment/Static folder
- Gameplay actors in /Gameplay/{Category} folders
- Tags: "destructible", "interactable", "physics"
-->

## Key Actors

<!-- WHY: Listing critical actors by exact label prevents the agent from accidentally
     moving or deleting essential scene elements (player start, game mode, sky setup). -->
<!-- Example:
- YourPlayerStart_0 -- player spawn point
- YourBP_GameMode -- custom game mode actor
- YourDirectionalLight_Sun -- main directional light, do not delete
-->
