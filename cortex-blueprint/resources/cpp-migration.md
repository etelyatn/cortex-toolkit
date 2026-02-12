# C++ Migration Guide

Decision framework and patterns for migrating Blueprint logic to C++.

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

## Migration Patterns

### Pattern 1: C++ Base + BP Subclass

Most common. Create C++ class with core logic, BP extends for customization.

```cpp
UCLASS(Blueprintable)
class AMyActor : public AActor
{
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Gameplay")
    float BaseDamage;

    UFUNCTION(BlueprintNativeEvent, Category = "Gameplay")
    void OnActivated();
};
```

BP subclass overrides `OnActivated` for specific behavior.

### Pattern 2: C++ Component

Extract logic into a component that BPs can attach.

```cpp
UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class UMyComponent : public UActorComponent
{
    UFUNCTION(BlueprintCallable, Category = "MySystem")
    void DoWork();
};
```

### Pattern 3: Function Library

Static utility functions accessible from any BP.

```cpp
UCLASS()
class UMyFunctionLibrary : public UBlueprintFunctionLibrary
{
    UFUNCTION(BlueprintCallable, Category = "Utils")
    static float CalculateValue(float Input);
};
```

## UE Coding Standards for Migration

- `UPROPERTY` for all Blueprint-visible variables
- `UFUNCTION(BlueprintCallable)` for functions BPs can call
- `UFUNCTION(BlueprintNativeEvent)` for functions BPs can override
- Category on every UPROPERTY and UFUNCTION
- No `LogTemp` — use project log category
