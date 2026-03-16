# Data Domain Context
> Fill in the sections below. Delete the HTML comment examples as you go.
> Agents read this file before every task.

## Tables

<!-- List your DataTables, CurveTables, StringTables, and DataAssets.
     WHY: Agents use this to avoid duplicates, choose the right container, and cross-reference tables.
     Example:
     - DT_WeaponStats: weapon definitions (Name, Damage, AttackSpeed, ItemTag) — reviewed weekly
     - DT_QuestData: quest definitions (QuestID, Title, RewardXP, RewardGold, RequiredLevel)
     - DT_EnemyDefinitions: enemy stats per tier (Health, Damage, XPReward, SpawnTag)
     - CT_LevelCurve: XP requirements per level (keys 1–50)
     - ST_UIText: localized UI strings (MainMenu, Settings, Quit, HUD labels)
     - DA_GameConfig: singleton DataAsset for global tuning values
-->

## Struct Definitions

<!-- Key struct schemas used by your DataTables.
     WHY: Agents use struct knowledge to create compatible rows without querying the editor.
     Field types must match UE property types exactly (FString, float, int32, FGameplayTag, etc.)
     Example:
     FWeaponStats (used by DT_WeaponStats):
       - Name: FString
       - Damage: float
       - AttackSpeed: float
       - ItemTag: FGameplayTag

     FQuestDefinition (used by DT_QuestData):
       - QuestID: FName
       - Title: FText
       - RewardXP: int32
       - RewardGold: int32
       - RequiredLevel: int32
       - QuestState: FGameplayTag
-->

## Balance Rules

<!-- Define acceptable value ranges and scaling rules.
     WHY: Agents use these as constraints when creating or reviewing data — outliers get flagged.
     Example:
     - Weapon Damage scales 1.15x per tier bracket (Tier 1–3, 4–6, 7–10)
     - No item should exceed 500 gold before level 15
     - Enemy HP = CT_LevelCurve value × 10 base
     - Quest XP reward: 50–200 per level bracket (1–10), 200–500 (11–20)
     - Drop rate probabilities per row must sum to 1.0
-->

## GameplayTags

<!-- Tag hierarchy and naming conventions.
     WHY: Agents validate tags before inserting them into DataTable rows.
     Example:
     - Item.Type.{Weapon|Armor|Consumable|Quest}
     - Item.Rarity.{Common|Uncommon|Rare|Epic|Legendary}
     - Quest.State.{Available|Active|Complete|Failed}
     - Enemy.Tier.{T1|T2|T3}
-->
