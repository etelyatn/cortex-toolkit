# C++ Migration Guide

Decision framework and concrete translation patterns for migrating Blueprint logic to C++.

## Quick Reference Tables

### Node Translation Table

| Blueprint Node | C++ Equivalent | Notes |
|---|---|---|
| Event BeginPlay | `virtual void BeginPlay() override;` | Call `Super::BeginPlay()` |
| Event Tick | `virtual void Tick(float DeltaTime) override;` | Set `PrimaryActorTick.bCanEverTick = true` |
| Branch | `if/else` | |
| Sequence | Statements in pin order | `Then 0`, `Then 1`, ... |
| ForEachLoop | `for (auto& Item : Array)` | |
| ForEachLoopWithBreak | ranged `for` + `break` | |
| WhileLoop | `while (Condition)` | |
| DoOnce | guard bool | `if (!bDidRun) { bDidRun = true; }` |
| Gate | bool-gated execution | open/close/toggle state |
| FlipFlop | toggling bool/branch | |
| SwitchOnInt | `switch` | |
| SwitchOnString | `if/else if` or `switch`-style map | |
| SwitchOnEnum | `switch` on enum | |
| Select | ternary or branch assignment | |
| MakeArray | initializer list / `TArray` push | |
| BreakStruct | field access | |
| MakeStruct | struct literal + assignments | |
| Get variable | direct member read | |
| Set variable | direct member write | |
| Cast To | `Cast<T>(Object)` | |
| IsValid | `IsValid(Object)` | |
| SpawnActor | `GetWorld()->SpawnActor<T>()` | |
| DestroyActor | `Destroy()` | |
| GetActorLocation | `GetActorLocation()` | |
| SetActorLocation | `SetActorLocation(NewLocation)` | |
| Call Function | direct function call | include module/header |
| Interface Call | `IInterface::Execute_Function(Target, ...)` | never direct virtual call from BP node |
| Print String | `UE_LOG(...)` or on-screen debug | no `LogTemp` |
| Timeline | `UTimelineComponent` + curve UPROPERTYs | see complex section |
| Event Dispatcher (Create) | `DECLARE_DYNAMIC_MULTICAST_DELEGATE_*` | select macro by param count |
| Event Dispatcher (Call) | `Dispatcher.Broadcast(...)` | |
| Event Dispatcher (Bind) | `Dispatcher.AddDynamic(...)` | |
| Event Dispatcher (Unbind) | `Dispatcher.RemoveDynamic(...)` | |
| Delay | `FTimerHandle` callback | latent translation |
| RetriggerableDelay | resettable timer handle | latent translation |
| MoveComponentTo | callback/timer chain | latent translation |
| AsyncLoadAsset | async callback path | latent translation |
| CreateDelegate | bind function pointer/delegate | |
| AssignDelegate | dynamic delegate bind | |
| InputAction | Enhanced Input binding | |
| Macro Instance | expand to native statements | no generic macro runtime |
| FunctionEntry | function signature | |
| FunctionResult | return/output writes | |

### Include Path Table

| Type | Include Path |
|---|---|
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
| UTimelineComponent | `Components/TimelineComponent.h` |
| UCurveFloat | `Curves/CurveFloat.h` |
| UCurveVector | `Curves/CurveVector.h` |
| UCurveLinearColor | `Curves/CurveLinearColor.h` |
| UUserWidget | `Blueprint/UserWidget.h` |
| UTextBlock | `Components/TextBlock.h` |
| UButton | `Components/Button.h` |
| UImage | `Components/Image.h` |
| UProgressBar | `Components/ProgressBar.h` |
| UWidgetAnimation | `Animation/WidgetAnimation.h` |
| UBlueprintFunctionLibrary | `Kismet/BlueprintFunctionLibrary.h` |
| UGameplayStatics | `Kismet/GameplayStatics.h` |
| UKismetMathLibrary | `Kismet/KismetMathLibrary.h` |
| UKismetSystemLibrary | `Kismet/KismetSystemLibrary.h` |
| FLatentActionInfo | `LatentActions.h` |
| FPendingLatentAction | `LatentActions.h` |
| FTimerHandle | `TimerManager.h` |
| FTimerManager | `TimerManager.h` |
| UInterface | `UObject/Interface.h` |
| UEnhancedInputComponent | `EnhancedInputComponent.h` |
| UInputAction | `InputAction.h` |
| UAITask_MoveTo | `Tasks/AITask_MoveTo.h` |
| FAIMoveRequest | `AITypes.h` |
| FOnTimelineEvent | `Components/TimelineComponent.h` |
| FOnTimelineFloat | `Components/TimelineComponent.h` |

### Module Dependency Table

| Construct | Typical Build.cs Dependencies |
|---|---|
| Core Actor/Component migration | `Core`, `CoreUObject`, `Engine` |
| UMG widgets | `UMG`, `Slate`, `SlateCore` |
| Timelines | `Engine` |
| Event dispatchers | `CoreUObject`, `Engine` |
| Latent actions (timers/system) | `Engine` |
| AI latent actions | `AIModule`, `NavigationSystem` |
| Interfaces | `CoreUObject`, `Engine` |
| Enhanced Input | `EnhancedInput` |

### Function Classification Table

| BP Pattern | UFUNCTION Specifier | When |
|---|---|---|
| C++ logic with BP override point | `BlueprintNativeEvent` | Keep default native behavior with optional BP override |
| Pure BP-defined implementation | `BlueprintImplementableEvent` | No native body needed |
| C++ API callable from BP | `BlueprintCallable` | BP should invoke, not override |

## Migration Decision Framework

### When to Migrate

| Signal | Priority |
|---|---|
| Profiler shows BP overhead in hot path | High |
| Logic duplicated across many Blueprints | High |
| Tick does non-trivial work every frame | High |
| Needs reusable base class API | Medium |
| Designer-iterated simple event hooks only | Keep in BP |

### Migration Outcomes

| Outcome | Action |
|---|---|
| Migrate | Generate new C++ class + reparent Blueprint |
| Merge | Patch existing C++ class |
| Improve | Replace weaker C++ logic with BP logic |
| Delete | Recommend deletion with evidence |
| Keep | Explain why BP should remain BP |

### BP Audit Patterns

- Duplication against existing C++ classes.
- No-op BP overrides that only call super.
- Dead/disconnected graph logic.
- Variable shadowing of parent members.
- Orphaned assets with no references.

## Migration Patterns (by BP type)

### Actor (C++ Base + BP Subclass)

- Generate `A*` class with constructor defaults and `BeginPlay`/`Tick` only when required.
- Reparent Blueprint and keep designer-tunable values as `EditAnywhere`.

### Component (UActorComponent subclass)

- Generate `U*Component` for reusable gameplay systems.
- Use `BlueprintSpawnableComponent` metadata where creation in editor is expected.

### FunctionLibrary (static utility)

- Generate `UBlueprintFunctionLibrary` with static helpers.
- Keep side-effect free math/utility methods here.

### Interface (UInterface + IInterface pair)

- Generate paired `UInterface` + `IInterface` classes.
- Define API on `IInterface`; call through `Execute_*`.

### Widget (UUserWidget + BindWidget)

- Use `BindWidget`/`BindWidgetOptional` and `BindWidgetAnim` (`Transient`).
- Bind delegates in `NativeConstruct()` with null checks.

## Complex Construct Translations

### Timeline -> UTimelineComponent

- Detect `UK2Node_Timeline`.
- Generate `UTimelineComponent` subobject + curve UPROPERTY references.
- Bind `FOnTimelineFloat` / vector / linear color delegates.
- Wire autoplay/loop/play rate flags from timeline template.
- Emit `TODO(MANUAL)` for curve asset extraction when keys are embedded in BP timeline.

### Event Dispatcher -> DECLARE_DYNAMIC_MULTICAST_DELEGATE

- Generate macro by parameter count (`_OneParam`, `_TwoParams`, etc.).
- Expose with `UPROPERTY(BlueprintAssignable)`.
- Translate call/bind/unbind to `Broadcast`, `AddDynamic`, `RemoveDynamic`.

### Latent Actions -> FTimerHandle / Callback Chains

- Detect latent metadata and known latent nodes.
- 1-2 sequential latent steps: callback chain with timers.
- 3+ sequential latent steps: explicit state machine.
- Always emit `TODO(VERIFY)` for latent approximations.

### Blueprint Interfaces -> UInterface + Execute_*

- Generate interface pair and implementation stubs where needed.
- Use `Target->GetClass()->ImplementsInterface(...)` before calls.
- Invoke with `IYourInterface::Execute_Function(Target, ...)`.

## Translation Patterns (for nodes not in the table)

### Engine API Call pattern

- `K2Node_CallFunction` -> direct C++ invocation with correct include/module.

### Cast Node pattern

- `K2Node_DynamicCast` -> `Cast<TargetClass>(Source)` with null guard.

### Macro Instance pattern

- `K2Node_MacroInstance` -> inline native control-flow structure.

### Struct Member Access pattern

- `K2Node_BreakStruct`/`K2Node_MakeStruct` -> direct field reads/writes.

## Error Handling

### TODO Severity Levels (MANUAL/VERIFY/OPTIMIZE)

- `TODO(MANUAL)`: no reliable translation; user must author final code.
- `TODO(VERIFY)`: approximate behavior generated; user must validate runtime equivalence.
- `TODO(OPTIMIZE)`: functionally correct, but improve performance/readability later.

Example format:

```cpp
// TODO(MANUAL): Extract BP timeline keys into a standalone UCurveFloat asset.
// TODO(VERIFY): Delay chain translated to timer callbacks; validate ordering and cancellation behavior.
// TODO(OPTIMIZE): Dispatcher broadcast currently per-tick; consider throttling.
```

## Known Limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| Complex graph flow | Approximate translation may be emitted | Add `TODO(VERIFY)` and user review |
| Custom latent actions (`FPendingLatentAction`) | Cannot be fully auto-translated | Emit `TODO(MANUAL)` with callback-pattern suggestion |
| No compile/build execution in migration agent output | Generated code not auto-verified | User compiles and validates after generation |
