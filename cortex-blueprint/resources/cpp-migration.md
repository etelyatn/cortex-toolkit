# C++ Migration Guide

Decision framework and patterns for migrating Blueprint logic to C++.

**Coding Standards:** All generated C++ must follow `docs/unreal-coding-standards.md` (Epic standard — PascalCase, Allman braces, tabs, UPROPERTY/UFUNCTION on everything Blueprint-visible).

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
- Use `meta = (BindWidget)` for required widgets, `meta = (BindWidgetOptional)` for optional
- Use `meta = (BindWidgetAnim)` with `Transient` for animation bindings
- Widget variable names must match the UMG designer widget names exactly
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
| **Delay** | **Unsupported in PoC** | Requires `FTimerHandle` + `SetTimer` |
| **Timeline** | **Unsupported in PoC** | Requires `UTimelineComponent` + `UCurveFloat` |
| **Event Dispatcher** | **Unsupported in PoC** | Requires `DECLARE_DYNAMIC_MULTICAST_DELEGATE` |

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

## BP Audit Patterns

When analyzing a Blueprint against existing C++ code, check for:

- **Duplication:** BP reimplements logic already in a C++ parent or sibling class
- **No-op overrides:** BP overrides a C++ function with identical or trivial logic (just calls Super)
- **Dead code:** Nodes with no execution path leading to them, disconnected subgraphs
- **Variable shadowing:** BP variable with same name as a parent C++ variable
- **Orphaned BP:** No other assets reference this Blueprint (check with `search_assets`)

## Known Limitations (PoC)

| Limitation | Impact | Future Work |
|-----------|--------|-------------|
| Timelines not supported | Agent warns and skips timeline nodes | Requires UTimelineComponent + UCurveFloat pattern |
| Latent actions not supported | Delay, MoveTo etc. skipped with warning | Requires FTimerHandle / async patterns |
| BP Interfaces not supported | Agent warns if BP implements interfaces | Requires multiple inheritance pattern |
| Event dispatchers not supported | Agent warns and skips | Requires DECLARE_DYNAMIC_MULTICAST_DELEGATE |
| Complex graph flow | May produce approximate translations | Flag for user review |
| No compilation validation | Generated code is not compiled/verified | Future: integrate with build system |

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
| SetNiagaraVariableLinearColor(FString) | UE 5.3 | SetNiagaraVariableLinearColor(FName) | Niagara variable setter nodes using FString parameter |
| TAssetPtr | UE 4.18 | TSoftObjectPtr | Variable type contains "TAssetPtr" |
| UProperty | UE 4.25 | FProperty | Reflect metadata referencing UProperty |
| BindAction (legacy input) | UE 5.1 | Enhanced Input system (UInputAction + UInputMappingContext) | Input binding nodes without Enhanced Input |

This table grows over time. Add entries when deprecated APIs are encountered during migrations.
