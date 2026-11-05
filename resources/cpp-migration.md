# C++ Migration Guide

Decision framework and patterns for migrating Blueprint logic to C++.

**Coding Standards:** All generated C++ must follow the consuming project's coding standards, if present (for example its own `docs/unreal-coding-standards.md`), otherwise Epic's Unreal standard — PascalCase, Allman braces, tabs, UPROPERTY/UFUNCTION on everything Blueprint-visible.

## When to Migrate

| Signal | Priority |
|--------|----------|
| Profiler shows BP overhead in hot path | High |
| Same logic duplicated across 5+ BPs | High |
| Tick function with heavy computation | High |
| Need base class for BP subclasses | Medium |
| Complex state machine with many branches | Medium |
| Simple event handler (overlap → action) | Don't migrate |
| Designer is actively iterating on logic | Don't migrate |

## Logic vs Cosmetic — What to Migrate

**The deciding factor is NOT the function name or node count. It is: does game logic depend on this value?**

### Moves to C++ (logic-driven)

Any operation where the value affects game state or other logic depends on it:
- Native state that hides an object during a game state change; Blueprint owns the UI visibility treatment. Native visibility mutation is appropriate when simulation depends on it.
- `SetLocation` to move an actor based on game state or player input — logic depends on position
- Native team/damage/status state; Blueprint owns the corresponding color, style, animation, and layout.
- State machines, branching, data processing, tick-driven computation
- Even a 2-node operation, if it's logic-driven, belongs in C++

### Stays in Blueprint (purely cosmetic)

Operations where NO other logic reads or reacts to the value:
- `SetColor` for decorative appearance nothing else checks — artist-owned
- `SetLocation/SetScale3D` to arrange mesh pieces for a door frame — decorative geometry
- `SetMaterial`, `SetStaticMesh`, `SetLightColor` for visual appearance — artist-owned
- `CreateDynamicMaterialInstance` + parameter setters — visual tuning
- Procedural geometry (door frames, wall segments) where no gameplay depends on positions
- Construction Script visual-sync nodes (see classification below)

**Key:** Separate state from rendering. Native owns state and simulation visibility where gameplay depends on it; Blueprint owns UI visibility, fades, styling, and other visual treatment of that state.

### Conversion Level Guidelines

**Minimal level:** Only migrate what is actively broken or measured as slow.

**Recommended level:** Migrate all logic-driven code. Keep purely cosmetic operations in BP.

**Everything level:** Migrate functionality within the ownership boundary; keep designer-owned presentation/defaults and visual-sync construction nodes in BP.

## Migration Outcomes

Not every Blueprint should be migrated. After analysis, classify into one of these outcomes:

| Outcome | When | Action |
|---------|------|--------|
| **Migrate** | BP has no C++ counterpart, logic belongs in C++ | Generate new C++ class, reparent BP |
| **Merge** | C++ class exists with partial overlap | Show diff, generate patch to extend existing C++ |
| **Improve** | C++ exists but BP has better/corrected logic | Show comparison, suggest C++ improvements |
| **Delete** | BP duplicates existing C++ exactly, or is garbage/unused | Recommend deletion with evidence |
| **Keep** | BP logic is appropriate as BP (designer iteration, simple events) | Explain why migration is not recommended |

## Migration Patterns

### Pattern 1: C++ Base + BP Subclass (Actor)

Most common. Create C++ class with core logic, BP extends for customization.

```cpp
UCLASS(Blueprintable)
class YOURMODULE_API AMyActor : public AActor
{
	GENERATED_BODY()

public:
	AMyActor();

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaTime) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Gameplay")
	float BaseDamage;

	UFUNCTION(BlueprintNativeEvent, Category = "Gameplay")
	void OnActivated();
};
```

**Constructor (required for every class):**

```cpp
AMyActor::AMyActor()
{
	PrimaryActorTick.bCanEverTick = true; // only if BP has Tick enabled

	// Default values from BP Class Defaults
	BaseDamage = 50.0f;
}
```

BP subclass overrides `OnActivated` for specific behavior.

### Pattern 2: C++ Component

Extract logic into a component that BPs can attach.

```cpp
UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class YOURMODULE_API UMyComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "MySystem")
	void DoWork();
};
```

### Pattern 3: Function Library

Static utility functions accessible from any BP.

```cpp
UCLASS()
class YOURMODULE_API UMyFunctionLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "Utils")
	static float CalculateValue(float Input);
};
```

### Pattern 4: Widget Blueprint (UUserWidget Subclass)

For migrating Widget Blueprints to C++. Use `BindWidget` to connect C++ to UMG designer widgets.

```cpp
UCLASS()
class YOURMODULE_API UMyWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UMyWidget(const FObjectInitializer& ObjectInitializer);

protected:
	virtual void NativePreConstruct() override; // design-time preview
	virtual void NativeConstruct() override;    // runtime initialization

	// BindWidget — the UMG designer must have a widget with this exact name
	UPROPERTY(BlueprintReadOnly, meta = (BindWidget))
	TObjectPtr<UTextBlock> TitleText;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidget))
	TObjectPtr<UButton> ConfirmButton;

	// Optional widget — won't crash if missing from designer
	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional))
	TObjectPtr<UImage> IconImage;

	// Animation binding — must match animation name in designer
	UPROPERTY(meta = (BindWidgetAnim), Transient)
	UWidgetAnimation* FadeInAnimation;

	UFUNCTION()
	void HandleConfirmClicked();
};
```

**Source file pattern:**

```cpp
UMyWidget::UMyWidget(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
}

void UMyWidget::NativeConstruct()
{
	Super::NativeConstruct();

	if (ConfirmButton)
	{
		ConfirmButton->OnClicked.AddDynamic(this, &UMyWidget::HandleConfirmClicked);
	}
}

void UMyWidget::HandleConfirmClicked()
{
	// Implementation here
}
```

**Key rules for Widget migration:**
- Use `meta = (BindWidget)` for required widgets, `meta = (BindWidgetOptional)` for optional. Only widgets the analysis reports with `is_variable: true` (the `entity_summary` widget entries) get native fields; `widgets` lists the whole tree, and layout-only widgets stay in the Designer.
- Use `meta = (BindWidgetAnim)` with `Transient` for animation bindings
- Choose clear role-based names before generation; rename native BindWidget fields and Designer widgets together using reference-aware Unreal operations. Names must match exactly; Designer widget classes must be assignment-compatible with the native property types. Keep styling/layout/animation authored in BP; expose semantic state through existing presentation hooks. See cortex-bp-migrate: Widget migration ownership and naming.
- Override `NativeConstruct()` for runtime init (replaces BP Construct event)
- Override `NativePreConstruct()` for design-time preview if needed
- Bind delegates in `NativeConstruct()` with null checks
- After migration, reparent the Widget BP to the new C++ class

### Pattern 4a: Widget Blueprint - Advanced Patterns

- Always pair dynamic delegate binding with unbind in `NativeDestruct()`
- Keep `BindWidget` for required controls and `BindWidgetOptional` for optional controls
- Use `BindWidgetAnim` only on transient `UWidgetAnimation*` fields
- Promote frequently observed UI state to `FieldNotify` properties where supported
- For ListView entry widgets, implement `IUserObjectListEntry` and keep entry object binding logic in C++
- Keep named slot content ownership in BP, but expose C++ helpers for slot-safe updates

### Widget Delegate Quick Reference

| Widget Type | Delegate | Notes |
|------------|----------|-------|
| UButton | `OnClicked` | Most common action event |
| UCheckBox | `OnCheckStateChanged` | Bool payload |
| USlider | `OnValueChanged` | Float payload |
| UComboBoxString | `OnSelectionChanged` | Selected option payload |
| UEditableText | `OnTextCommitted` | Commit method aware |
| UEditableTextBox | `OnTextChanged` | Live edit updates |
| USpinBox | `OnValueChanged` | Numeric input |
| UListView | `OnItemClicked` | Item-driven list behavior |

### Widget Migration Decision Override

Keep widget label references and localized format templates in editable Widget Blueprint FText defaults; preserve String Table IDs/keys and format arguments. Native code selects the appropriate label and formats dynamic values. Verify defaults after save/reload against the final native parent rather than copying table paths/keys into constructors.

| Condition | Override Decision |
|----------|-------------------|
| Widget is layout-only with style tweaks | Keep BP |
| Widget has heavy logic in EventGraph | Migrate logic to C++ |
| Widget binds many delegates but little logic | Hybrid (C++ wiring + BP visuals) |
| Widget uses complex animation choreography | Keep animation orchestration in BP |

## Function Classification

| BP Pattern | C++ Specifier | When |
|-----------|--------------|------|
| Function with logic that BP should override | `BlueprintNativeEvent` | Logic benefits from C++, BP needs override point. Generates `_Implementation` virtual. |
| Function only for BP to implement | `BlueprintImplementableEvent` | No C++ body, pure BP override point |
| Final C++ logic, BP calls only | `BlueprintCallable` | BP should not override, just call |

## Common Blueprint Node → C++ Translations

| Blueprint Node | C++ Equivalent | Notes |
|---------------|---------------|-------|
| **Event BeginPlay** | `virtual void BeginPlay() override;` | Call `Super::BeginPlay()` |
| **Event Tick** | `virtual void Tick(float DeltaTime) override;` | Call `Super::Tick()`, set `bCanEverTick` in constructor |
| **Branch** | `if (Condition) { } else { }` | |
| **Sequence** | Statements in order | Emit in pin order (Then 0, Then 1, ...) |
| **ForEachLoop** | `for (auto& Item : Array) { ... }` | |
| **WhileLoop** | `while (Condition) { ... }` | |
| **Gate** | `if (bGateOpen)` with bool state | |
| **DoOnce** | `if (!bHasDone) { bHasDone = true; ... }` | |
| **SwitchOnInt/String/Enum** | `switch (Value) { case ...: }` | Or `if/else if` chains |
| **Get/Set variable** | Direct member access (`MyVariable = Value;`) | |
| **Cast To** | `Cast<ATargetClass>(Actor)` | |
| **Is Valid** | `IsValid(Object)` or `if (Object)` | |
| **Print String** | `UE_LOG(LogYourModule, Log, TEXT("%s"), *Message);` | Or `GEngine->AddOnScreenDebugMessage()` |
| **Spawn Actor** | `GetWorld()->SpawnActor<AMyClass>(SpawnParams);` | |
| **Destroy Actor** | `Destroy();` | |
| **Get/Set Actor Location** | `GetActorLocation()` / `SetActorLocation(NewLocation)` | |
| **Get Player Controller** | `UGameplayStatics::GetPlayerController(this, 0)` | |
| **Create Widget** | `CreateWidget<UMyWidget>(GetOwningPlayer());` | |
| **Add to Viewport** | `Widget->AddToViewport();` | |
| **Delay** | `FTimerHandle` + `GetWorldTimerManager().SetTimer(...)` | Callback-based; chain multiple for sequential delays |
| **Timeline** | `UTimelineComponent*` + `UCurveFloat*`/`UCurveVector*`/`UCurveLinearColor*` | Declare component as UPROPERTY, bind delegates in BeginPlay |
| **Event Dispatcher** | `DECLARE_DYNAMIC_MULTICAST_DELEGATE(...)` + `UPROPERTY(BlueprintAssignable)` | 0-9 param variants available |

## Common Include Paths

| Type | Include Path |
|------|-------------|
| AActor | `GameFramework/Actor.h` |
| APawn | `GameFramework/Pawn.h` |
| ACharacter | `GameFramework/Character.h` |
| APlayerController | `GameFramework/PlayerController.h` |
| UActorComponent | `Components/ActorComponent.h` |
| USceneComponent | `Components/SceneComponent.h` |
| UStaticMeshComponent | `Components/StaticMeshComponent.h` |
| USkeletalMeshComponent | `Components/SkeletalMeshComponent.h` |
| UCapsuleComponent | `Components/CapsuleComponent.h` |
| UBoxComponent | `Components/BoxComponent.h` |
| USphereComponent | `Components/SphereComponent.h` |
| UUserWidget | `Blueprint/UserWidget.h` |
| UTextBlock | `Components/TextBlock.h` |
| UButton | `Components/Button.h` |
| UImage | `Components/Image.h` |
| UProgressBar | `Components/ProgressBar.h` |
| UWidgetAnimation | `Animation/WidgetAnimation.h` |
| UBlueprintFunctionLibrary | `Kismet/BlueprintFunctionLibrary.h` |
| UGameplayStatics | `Kismet/GameplayStatics.h` |
| UKismetMathLibrary | `Kismet/KismetMathLibrary.h` |
| FTimerHandle | `TimerManager.h` |

## Blueprint Cleanup Tools

### cleanup_migration

Reparents a Blueprint to a new C++ class and removes migrated variables and functions in a single operation. This is the primary cleanup command used after the C++ class is built and compiled. Run it on the original Blueprint, in place.

```python
blueprint_cmd(command="cleanup_migration", params={
    "asset_path": "/Game/Blueprints/BP_Enemy",
    "new_parent_class": "/Script/MyGame.AEnemyBase",
    "remove_variables": ["Health", "MoveSpeed"],
    "remove_functions": ["CalculateDamage", "OnHit"],
    "compile": True,   # default
    "save": False,     # default is True: stage in memory so the migration stays reversible
})
# Returns:
# {
#   "reparented": true,
#   "new_parent": "AEnemyBase",
#   "removed_variables": ["Health", "MoveSpeed"],
#   "removed_functions": ["CalculateDamage", "OnHit"],
#   "compiled": true,
#   "compile_status": "UpToDate",
#   "warnings": []
# }
```

**Parameters:**
- `asset_path`: Blueprint asset path (required)
- `new_parent_class`: Full class path to reparent to (e.g., `/Script/MyGame.AEnemyBase`). Optional — omit to skip reparenting.
- `remove_variables`: List of variable names to remove. Optional. Non-existent names are silently skipped and added to `warnings`.
- `remove_functions`: List of function graph names to remove. Optional. Non-existent names are silently skipped and added to `warnings`.
- `migrated_overrides`: Overrides already migrated. Optional.
- `compile` (default `true`): Compile the Blueprint after all mutations
- `save` (default `true`): Writes the whole package, including earlier staged edits. The migration pipeline passes `false` so `core_cmd` `reload_asset` can still discard the migration; compile errors prevent saving either way.

**Reparent type safety:** Only same-family reparenting is allowed:
- Actor → Actor subclass
- ActorComponent → ActorComponent subclass
- UserWidget → UserWidget subclass

Cross-family reparenting (e.g., Actor → Component) returns `InvalidField`.

**Error cases:**
- `BlueprintNotFound`: Asset path not found
- `InvalidField`: Missing `asset_path`, parent class not found, or type-family mismatch
- `SaveFailed`: Package could not be saved to disk

## SCS Component Migration

When migrating Blueprint SCS components (Components panel) to C++ `CreateDefaultSubobject` declarations, first inspect `analyze_for_migration.scs_collisions`. Adoptable collisions can be resolved by setting the inherited C++ property default to the owned SCS template with `set_class_defaults` using the recommended qualified value such as `OpenSeq@self`. Blocking collisions should be renamed with `rename_scs_component` before reparenting or cleanup.

After the C++ class is created and the Blueprint is reparented, remove redundant SCS entries with `remove_scs_component`.

### Workflow: Migrate a Blueprint Component to C++

```
1. Run analyze_for_migration and inspect scs_collisions
2. For adoptable collisions, run set_class_defaults with recommended_params (often Name@self)
3. For blocking collisions, run rename_scs_component with the recommended new_name
4. Generate C++ class with CreateDefaultSubobject in constructor
5. Build project
6. cleanup_migration — reparent Blueprint to new C++ class
7. remove_scs_component — delete the now-redundant SCS node
8. `blueprint_cmd(command="compile", params={"asset_path": "..."})` — verify clean compile
```

**Example:**

```python
# After C++ class is built and Blueprint is reparented:
remove_scs_component(
    asset_path="/Game/Blueprints/BP_JumpPad",
    component_name="StaticMeshComponent0",
    compile=True
)
# Returns: {"removed_component": "StaticMeshComponent0", "compiled": true, "compile_status": "UpToDate"}
```

**Parameters:**
- `asset_path`: Blueprint asset path
- `component_name`: Variable name shown in the Components panel (matches the SCS node's variable name)
- `compile` (default `true`): Compile after removal
- `acknowledged_losses`: Echo the exact `required_acknowledgment` array after a
  `POTENTIAL_DATA_LOSS` refusal and explicit user confirmation.
- `force`: Explicit override for dirty instanced sub-object loss; avoid unless requested.

**Error cases:**
- `ComponentNotFound`: The component name was not found in the SCS — check the exact variable name via `blueprint_cmd` `get_info`
- `InvalidField` (code): Blueprint has no SCS — only Actor-based Blueprints have SCS; component and widget Blueprints do not
- `POTENTIAL_DATA_LOSS`: Dirty instanced sub-object state would be lost. Surface the
  `dirty_details` and `required_acknowledgment` to the user before retrying.
- `COMPILE_FAILED`: The post-removal compile failed; the command rolls back and does not save.

**Child component handling:** If the removed component has children in the hierarchy, they are automatically re-parented to the removed node's parent. No manual child re-wiring is needed.

## Backup, Save, and Recompile

These commands support the FINALIZE and COMPLETE phases of the migration pipeline. The Blueprint is migrated **in place**: it is never renamed, moved, or replaced by a copy.

### Why the original is never renamed

`IAssetTools::RenameAssets` runs `FAssetRenameManager::FixReferencesAndRename` (Engine/Source/Developer/AssetTools/Private/AssetRenameManager.cpp), which loads and rewrites every referencer to the renamed asset's path. Renaming `BP_Enemy` to `BP_Enemy_Backup` therefore moves every referencer onto the backup, and renaming a migrated copy to `BP_Enemy` afterwards does not move them back. Reparent the original in place instead.

### duplicate (backup snapshot)

Creates `BP_Name_Backup` before the first mutation. A duplicate has no referencers; it is a read-only snapshot for comparison, not a restore source. `duplicate` only marks the package dirty, so save it right away (`blueprint_cmd(command="save", params={"asset_path": "/Game/Blueprints/BP_Enemy_Backup"})`) and verify with `core_cmd(command="asset_fingerprint", params={"paths": ["/Game/Blueprints/BP_Enemy_Backup"]})` (non-empty `package_saved_hash`, `is_dirty: false`); the PREPARE editor restart discards unsaved assets.

Placed level instances reference the original, not the backup, so when `get_referencers` shows level placements also export their per-instance overrides before the first mutation: `level_cmd(command="export_class_instances", params={"class": "/Game/Blueprints/BP_Enemy", "maps": ["/Game/Maps/Main"], "out_path": "<project>/Saved/Migration/BP_Enemy_placed_instances_baseline.json"})`. The verifier runs the same export afterwards and diffs the two reports.

```python
blueprint_cmd(command="duplicate", params={
    "asset_path": "/Game/Blueprints/BP_Enemy",
    "new_name": "BP_Enemy_Backup",
    "new_path": "/Game/Blueprints",
})
```

**Parameters:** `asset_path` (source), `new_name`, `new_path` — all required.

### save

Writes the Blueprint package. Used twice in the pipeline: on the backup right after `duplicate`, and on the migrated Blueprint once, after the final clean compile (earlier `remove_scs_component` / `rename_scs_component` calls may already have written that package).

```python
blueprint_cmd(command="save", params={"asset_path": "/Game/Blueprints/BP_Enemy"})
```

Commands that always write the package without a `save` option: `rename_scs_component`, `remove_scs_component`.

### recompile_dependents

Recompiles all Blueprints that depend on the given Blueprint. Call after the Blueprint is saved to clear stale data caused by the class-layout change.

```python
blueprint_cmd(command="recompile_dependents", params={
    "asset_path": "/Game/Blueprints/BP_Enemy"
})
# Returns:
# {
#   "asset_path": "/Game/Blueprints/BP_Enemy",
#   "dependent_count": 3,
#   "recompiled_count": 3,
#   "results": [
#     {"blueprint": "/Game/Blueprints/BP_EnemyBoss", "status": "success", "errors": []},
#     {"blueprint": "/Game/Blueprints/BP_EnemyMinion", "status": "success", "errors": []},
#     ...
#   ]
# }
```

**Parameters:**
- `asset_path`: The Blueprint whose dependents should be recompiled

**Result fields per dependent:**
- `blueprint`: Full object path of the dependent
- `status`: `"success"` or `"error"`
- `errors`: Array of error strings (empty on success)

**Error cases:** `BlueprintNotFound` if `asset_path` does not exist.

**Side effect:** the command recompiles dependents but does not save them, so each recompiled dependent is left dirty in the editor. Report them and either save each explicitly (`blueprint_cmd` `save`) with the user's agreement or state that a later Save All will include them.

### rename (archiving the backup only)

Only the backup snapshot may be renamed or moved, because it has no referencers. Use this to archive it:

```python
blueprint_cmd(command="rename", params={
    "source_path": "/Game/Blueprints/BP_Enemy_Backup",
    "dest_path": "/Game/Migration/Backups/BP_Enemy_Backup",
})
```

`rename` leaves one redirector at the source path. It has no referencers and is harmless; leave it. Do not run `fixup_redirectors` as part of a migration: it is folder-wide and recursive by default and force-deletes unreferenced redirectors and rewrites referencers of the rest, which can touch unrelated assets. If cleanup is wanted, list first with `core_cmd(command="list_redirectors", params={"path": "/Game/Blueprints", "recursive": false})`, show the result to the user, and fix up only that single redirector path after explicit confirmation. Never use `rename` on the migrated Blueprint.

### compare_blueprints

Structurally compares two Blueprints and returns a list of differences. Used in the VERIFY phase to compare the read-only backup snapshot against the in-place migrated Blueprint. The differences must be exactly the migrated members. Run it only after the migrated Blueprint compiles clean (known crash vector on recently reparented Blueprints with stale references, Issue 99); verification must not depend on it.

```python
blueprint_cmd(command="compare_blueprints", params={
    "source_path": "/Game/Blueprints/BP_Enemy_Backup",
    "target_path": "/Game/Blueprints/BP_Enemy"
})
# Returns:
# {
#   "match": true,
#   "source_path": "...",
#   "target_path": "...",
#   "differences": [],
#   "summary": {"total_checks": 12, "matches": 12, "differences": 0}
# }
```

**Parameters:**
- `source_path`: Baseline Blueprint (the pre-migration backup snapshot)
- `target_path`: Blueprint to compare against the baseline
- `sections` (optional): Array to restrict comparison — valid values: `"variables"`, `"functions"`, `"components"`, `"cdo"`

**Sections compared by default (all four):**
- `variables` — variable names, types, and default values
- `functions` — function graph presence on each side
- `components` — SCS component names and classes
- `cdo` — CDO property values for all Blueprint-visible properties

**Difference entry fields:**
- `section`: Which section the difference is in
- `item`: Variable/function/component/property name
- `message`: Human-readable description
- `source_value`: Value from source Blueprint
- `target_value`: Value from target Blueprint

**Example with sections filter:**
```python
blueprint_cmd(command="compare_blueprints", params={
    "source_path": "/Game/Blueprints/BP_Enemy_Backup",
    "target_path": "/Game/Blueprints/BP_Enemy",
    "sections": ["variables", "components"]
})
```

**Error cases:** `BlueprintNotFound` if either path does not exist; `InvalidField` if params are missing.

## BP Audit Patterns

When analyzing a Blueprint against existing C++ code, check for:

- **Duplication:** BP reimplements logic already in a C++ parent or sibling class
- **No-op overrides:** BP overrides a C++ function with identical or trivial logic (just calls Super)
- **Dead code:** Nodes with no execution path leading to them, disconnected subgraphs
- **Variable shadowing:** BP variable with same name as a parent C++ variable
- **Orphaned BP:** No other assets reference this Blueprint (check with `search_assets`)

## Known Limitations

| Limitation | Impact | Workaround |
|-----------|--------|------------|
| Complex graph flow | May produce approximate translations | Flag for user review |
| Latent action chains (3+) | Sequential delays/MoveTo require state machine pattern | Agent generates state enum + switch for 3+ latent chains |
| Blueprint-only parent chain | Cannot reparent to C++ if parent is also a Blueprint | Migrate parent first, then children |

## UE Coding Standards for Migration

- `UPROPERTY` for all Blueprint-visible variables with `Category`
- `UFUNCTION(BlueprintCallable)` for functions BPs can call
- `UFUNCTION(BlueprintNativeEvent)` for functions BPs can override (generates `_Implementation`)
- `UFUNCTION(BlueprintImplementableEvent)` for pure BP override points (no C++ body)
- `GENERATED_BODY()` in every UCLASS
- `YOURMODULE_API` export macro on all classes
- Constructor with default values from BP Class Defaults
- No `LogTemp` — use project log category
- PascalCase naming, Allman braces, tabs for indentation
- Forward declare in .h where possible, full includes in .cpp only
- `#pragma once` header guard
- Correct parent class from BP analysis (never hardcode AActor)

## Deprecated API Patterns

Cross-reference these against Blueprint analysis results during migration. Flag matches in the preview before generating C++ code. Use the modern replacement API in all generated code.

| Pattern | Deprecated Since | Replacement | Detection Signal |
|---------|-----------------|-------------|-----------------|
| SetNiagaraVariableLinearColor(FString) | UE 5.1 | SetNiagaraVariableLinearColor(FName) | Niagara variable setter nodes using FString parameter |
| TAssetPtr | UE 4.18 | TSoftObjectPtr | Variable type contains "TAssetPtr" |
| UProperty | UE 4.25 | FProperty | Reflect metadata referencing UProperty |
| BindAction (legacy input) | UE 5.1 | Enhanced Input system (UInputAction + UInputMappingContext) | Input binding nodes without Enhanced Input |
| FHitResult::Actor | UE 5.0 | FHitResult::GetActor() | Direct access to FHitResult.Actor weak pointer field |

This table grows over time. Add entries when deprecated APIs are encountered during migrations.

## Migration Artifacts

A migration produces at most three files under `docs/migration/blueprint-to-cpp/{BP_Name}/`: `migration-plan.md` (the primary document, updated through every stage), `design.md` (optional, complex migrations only) and `rollback.json` (machine-readable restore information). Do not write per-section JSON files (`01-pre-migration.json` through `05-rollback.json`) or a merged `report.json`; all of that data lives inline in `migration-plan.md`. The artifact rules in the cortex-bp-migrate skill are authoritative.

## V5 Verification Checklist

- Structural compare completed (`compare_blueprints`)
- Property and default-value parity reviewed
- Logic coverage validated for migrated groups
- Dependency impact checked (children/referencers)
- Level instance behavior sanity-checked
- Dependents recompiled after the in-place save

## Medium-Level Component Classification

| Component Case | Medium-Level Handling |
|---------------|-----------------------|
| Core identity/capability component | Migrate declaration to C++ (`CreateDefaultSubobject`) |
| Asset/config-only component tuning | Keep values in BP Class Defaults |
| Visual-only designer component | Keep in BP unless needed for reusable base behavior |
| Complex runtime logic in component graph | Migrate logic to C++; keep editor-facing tuning in BP |

## Visual Sync Classification (Construction Script)

During migration analysis, classify `UserConstructionScript` nodes into two buckets. These are hard rules — not heuristics.

### ALWAYS Stays in Blueprint UserConstructionScript

These operations encode material-specific slot indices, effect parameter names, or visual tuning values owned by artists/designers. Moving them to C++ creates unnecessary coupling.

| Function | Reason |
|----------|--------|
| `SetDefaultCustomPrimitiveDataFloat` | Material slot index — asset-internal knowledge |
| `SetDefaultCustomPrimitiveDataVector4` | Material slot index — asset-internal knowledge |
| `SetNiagaraVariable*` (any variant) | Effect parameter name — designer-owned |
| `SetLightColor` | Visual tuning |
| `SetIntensity` | Visual tuning |
| `SetMaterial`, `SetMaterialByName` | Material slot assignment |
| `SetScalarParameterValue` | Dynamic material instance parameter |
| `SetVectorParameterValue` | Dynamic material instance parameter |
| `SetTextureParameterValue` | Dynamic material instance parameter |
| `CreateDynamicMaterialInstance` | Must stay paired with its parameter setters |
| `SetStaticMesh`, `SetSkeletalMesh` | Visual asset assignment |
| `SetVisibility`, `SetHiddenInGame` | Visual toggle |
| `SetCustomDepthStencilValue` | Rendering feature tied to visual effects |

General heuristic: if the function's primary purpose is controlling what the player sees and the values are iterated on by artists/designers, it stays in Blueprint.

### Moves to C++ OnConstruction

- Component transforms (`SetRelativeLocation`, `SetWorldScale3D`, etc.)
- `AddTag`, `SetCollisionProfileName`, `SetGenerateOverlapEvents`
- Pure gameplay state initialization with no asset-internal knowledge

### Rules

- If `UserConstructionScript` contains ONLY visual-sync nodes, do NOT generate `OnConstruction()` at all.
- `OnConstruction` (C++) runs before `UserConstructionScript` (BP) in the construction pipeline — they are sequential, not independent. BP visual sync can depend on state set by C++ structural init.
- For actors with 500+ level instances, flag visual sync as a performance recommendation in the migration report, but default to keeping in Blueprint for designer accessibility.

### Migration Plan Schema

Visual sync items use `target: "blueprint"` with `reason: "visual_sync"`:

```json
{
  "name": "SetLightColor chain",
  "kind": "construction_script_nodes",
  "target": "blueprint",
  "reason": "visual_sync",
  "pass": null,
  "group": "Visual Feedback"
}
```

## Cleanup Order Rule

When removing migrated Blueprint content, always clean consumers before producers:
1. Reparent to C++ class
2. Disconnect migrated event graph nodes — use `graph_cmd` `disconnect` to break the exec
   output pin on each event entry node (the pin name comes from `get_subgraph`, normally `then`),
   then remove the dead chains with `blueprint_cmd` `delete_orphaned_nodes` (event entry nodes
   are preserved). Never delete nodes one by one with `graph.remove_node`.
3. Remove migrated functions — verify compile after each
4. Remove migrated variables — verify compile after each
5. Remove migrated SCS components — verify compile after each

## V6 Migration Pipeline

The migration workflow uses a 4-stage pipeline:

| Stage | Purpose | Gate |
|-------|---------|------|
| **ANALYZE** | Conversational goals + technical analysis → migration design | User approves design |
| **PLAN** | Generate granular task list with complete C++ code | User approves plan |
| **EXECUTE** | Run phase workflows with checkpoint verification | Auto-verify checkpoint |
| **COMPLETE** | Verify, present results, save, backup decision, final report | User approves finalize |

Entry point: `/cortex-bp-migrate <BlueprintPath>` (supports `--audit` and `--resume`)

### Plan Document

Location: `docs/migration/blueprint-to-cpp/{BP_Name}/migration-plan.md`

The plan document has YAML frontmatter for machine-readable state (status, current_task, failed_task, phase) and a markdown body with numbered tasks. Generated C++ code lives in `docs/migration/blueprint-to-cpp/{BP_Name}/generated/`.

Key principle: all C++ code is generated during PLAN stage. The EXECUTE stage writes pre-generated code to disk — it does not derive code on the fly.

### Design Reference

- Pipeline design and phase guides: the `cortex-bp-migrate` skill and `resources/bp-migration-*.md`
