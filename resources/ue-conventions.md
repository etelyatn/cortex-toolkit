# Unreal Engine Conventions

Reference for UE coding standards relevant to UnrealCortex projects.

## Naming Prefixes

| Prefix | Type | Example |
|--------|------|---------|
| `F` | Structs, value types | `FVector`, `FQuestInfo` |
| `U` | UObject-derived classes | `UDataTable`, `UCortexSettings` |
| `A` | AActor-derived classes | `APlayerCharacter` |
| `E` | Enums | `EQuestState` |
| `I` | Interfaces | `ICortexDomainHandler` |
| `T` | Templates | `TArray`, `TMap` |

## Asset Naming

| Type | Pattern | Example |
|------|---------|---------|
| DataTable | `DT_{SystemName}` | `DT_QuestData` |
| DataAsset | `DA_{Name}` | `DA_WeaponConfig` |
| CurveTable | `CT_{Name}` | `CT_LevelCurve` |
| Blueprint | `BP_{Type}_{Name}` | `BP_Actor_TreasureChest` |
| Widget Blueprint | `WBP_{ScreenName}` | `WBP_MainMenu` |
| Material Instance | `MI_{Name}` | `MI_WoodFloor` |
| StringTable | `ST_{Name}` | `ST_UIStrings` |

## Code Organization

```
Plugins/UnrealCortex/Source/{ModuleName}/
├── Public/             ← headers, interfaces
│   ├── {ModuleName}Module.h
│   └── Operations/     ← operation class headers
├── Private/            ← implementations
│   ├── {ModuleName}Module.cpp
│   ├── Operations/     ← operation implementations
│   └── Tests/          ← automation tests
└── {ModuleName}.Build.cs
```

## Logging

- Core: `LogCortex`
- Domain modules: `LogCortex{Domain}` (e.g., `LogCortexData`)
- Never use `LogTemp`
- Define in module header, include in implementation files

## Key Patterns

- **Game Thread access:** All UObject operations via `AsyncTask(ENamedThreads::GameThread, ...)`
- **Transaction support:** Wrap writes in `FScopedTransaction` for undo/redo
- **LoadObject guard:** Always check `FindPackage` + `DoesPackageExist` before `LoadObject`
- **Test cleanup:** `MarkAsGarbage()` for all created UObjects
- **Blueprint persistence:** `SavePackage()` after creating Blueprint assets
