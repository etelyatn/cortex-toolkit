# UE API Recipes

Verified programmatic Unreal Engine patterns for AI agents. Each recipe documents a known-wrong AI-generated pattern, the correct version, and why the wrong pattern fails silently.

**Add a recipe** when a plan or implementation uses a wrong UE API pattern. Keep this battle-tested, not speculative.

---

## Blueprint Creation

### Recipe 1: `FKismetEditorUtilities::CreateBlueprint` — Blueprint Class Parameter Matrix

**What:** Creating a Blueprint asset programmatically requires different `BlueprintClass` and `GeneratedClassClass` arguments depending on the BP type. Using wrong types creates a Blueprint that looks like it succeeded but has the wrong runtime behavior.

**Wrong pattern (AI commonly generates this for all BP types):**
```cpp
// WRONG — always uses UBlueprint + UBlueprintGeneratedClass
// Creates a UBlueprint, but Widget/Component/Interface BPs require specific subclasses
UBlueprint* BP = FKismetEditorUtilities::CreateBlueprint(
    ParentClass,
    Package,
    FName(TEXT("WBP_Test")),
    BPTYPE_Normal,
    UBlueprint::StaticClass(),               // <-- WRONG for Widget/Component/Interface
    UBlueprintGeneratedClass::StaticClass()); // <-- WRONG for Widget
// IsA(WidgetBlueprintClass) → false, WidgetTree → nullptr
```

**Correct parameter matrix:**

| BP Type | `ParentClass` | `BlueprintType` | `BlueprintClass` | `GeneratedClassClass` |
|---------|--------------|-----------------|------------------|-----------------------|
| Actor | `AActor` or subclass | `BPTYPE_Normal` | `UBlueprint::StaticClass()` | `UBlueprintGeneratedClass::StaticClass()` |
| Widget | `UUserWidget` or subclass | `BPTYPE_Normal` | `FindObject<UClass>(nullptr, TEXT("/Script/UMGEditor.WidgetBlueprint"))` | `UBlueprintGeneratedClass::StaticClass()` ¹ |
| Component | `UActorComponent` or subclass | `BPTYPE_Normal` | `UBlueprint::StaticClass()` | `UBlueprintGeneratedClass::StaticClass()` |
| Interface | `UInterface` | **`BPTYPE_Interface`** | `UBlueprint::StaticClass()` | `UBlueprintGeneratedClass::StaticClass()` |
| FunctionLibrary | `UBlueprintFunctionLibrary` | **`BPTYPE_FunctionLibrary`** | `UBlueprint::StaticClass()` | `UBlueprintGeneratedClass::StaticClass()` |

> **Critical:** Interface and FunctionLibrary use non-`Normal` `BlueprintType` values. Passing `BPTYPE_Normal` for either creates a Blueprint that compiles silently but fails at runtime — the engine uses `BP->BlueprintType` to route interface-specific compilation, event graph filtering, and editor toolbar state. This is the most common AI mistake with this API.

**Correct pattern (Widget Blueprint):**
```cpp
// CORRECT — use FindObject to resolve UMGEditor classes at runtime
static UClass* WidgetBlueprintClass = FindObject<UClass>(
    nullptr, TEXT("/Script/UMGEditor.WidgetBlueprint"));

UBlueprint* BP = FKismetEditorUtilities::CreateBlueprint(
    UUserWidget::StaticClass(),
    Package,
    FName(TEXT("WBP_Test")),
    BPTYPE_Normal,
    WidgetBlueprintClass,                    // <-- Widget-specific Blueprint class
    UBlueprintGeneratedClass::StaticClass());
// IsA(WidgetBlueprintClass) → true, WidgetTree → valid
```

¹ Widget Blueprints technically generate `UWidgetBlueprintGeneratedClass`, but passing `UBlueprintGeneratedClass::StaticClass()` here is accepted by the engine and confirmed working in `CortexBPAssetOps.cpp`. The engine substitutes the correct class internally.

**Why:** `UWidgetBlueprint` is defined in the `UMGEditor` module, which is editor-only. Engine code that creates Widget BPs must use `FindObject<UClass>` rather than including the header directly. Using `UBlueprint::StaticClass()` creates a plain `UBlueprint` — it compiles, but `Cast<UWidgetBlueprint>()` returns null and the WidgetTree is never initialized.

**Source:** `Plugins/UnrealCortex/Source/CortexBlueprint/Private/Operations/CortexBPAssetOps.cpp`

---

## Dynamic Class Resolution

### Recipe 2: `FindObject<UClass>` — Resolving Editor/Plugin Classes Without Compile-Time Dependencies

**What:** When a module must work with classes from editor-only or optional plugin modules (UMGEditor, CommonUI, GameplayAbilities), use `FindObject<UClass>` to avoid hard compile-time dependencies.

**Wrong pattern (AI commonly generates direct includes):**
```cpp
// WRONG — adds UMGEditor as a hard dependency to a runtime module
#include "WidgetBlueprint.h"  // Pulls in UMGEditor — causes link errors in non-editor builds

UClass* WidgetBPClass = UWidgetBlueprint::StaticClass(); // Hard dependency
```

**Correct pattern (short-lived context, e.g., a single command handler):**
```cpp
// CORRECT — resolve at runtime, no compile-time dependency
// For short-lived call sites: static local is fine (see hot reload caveat below)
static UClass* WidgetBlueprintClass = nullptr;
if (!WidgetBlueprintClass)
{
    // Note: FindObject returns nullptr if UMGEditor hasn't loaded yet (e.g., during StartupModule)
    WidgetBlueprintClass = FindObject<UClass>(nullptr, TEXT("/Script/UMGEditor.WidgetBlueprint"));
}

if (!WidgetBlueprintClass)
{
    // UMGEditor not loaded — handle gracefully
    return;
}

if (Asset->IsA(WidgetBlueprintClass))
{
    // Safe to treat as Widget Blueprint
}
```

**Hot reload caveat:** `static UClass*` locals are initialized once per process. After a hot reload, the cached pointer refers to the old (GC'd) class at a stale address — this causes crashes or silent type mismatches. For long-lived objects (subsystems, module-level caches), use `TWeakObjectPtr<UClass>` instead:
```cpp
// For long-lived caches: use TWeakObjectPtr to survive hot reload
static TWeakObjectPtr<UClass> WidgetBlueprintClassPtr;
UClass* WidgetBlueprintClass = WidgetBlueprintClassPtr.Get();
if (!WidgetBlueprintClass)
{
    WidgetBlueprintClass = FindObject<UClass>(nullptr, TEXT("/Script/UMGEditor.WidgetBlueprint"));
    WidgetBlueprintClassPtr = WidgetBlueprintClass;
}
```

**Common paths to resolve:**

| Class | Path |
|-------|------|
| `UWidgetBlueprint` | `/Script/UMGEditor.WidgetBlueprint` |
| `UUserWidget` | `/Script/UMG.UserWidget` |
| `UCommonActivatableWidget` | `/Script/CommonUI.CommonActivatableWidget` |
| `UGameplayAbility` | `/Script/GameplayAbilities.GameplayAbility` |

**Why:** `FindObject` searches the currently-loaded class pool at runtime. This works because UMGEditor is always loaded in the editor, where you'd use this class. In cooked builds, the editor module isn't present — but you'd never need `UWidgetBlueprint` at runtime anyway.

**Thread safety:** `FindObject` is not thread-safe — call it on the Game Thread only. All Cortex operations already dispatch to the Game Thread via `AsyncTask(ENamedThreads::GameThread)`, so this is always safe in context.

**Source:** `Plugins/UnrealCortex/Source/CortexBlueprint/Private/Operations/CortexBPAssetOps.cpp` (multiple call sites)

---

## Test Asset Lifecycle

### Recipe 3: `MarkAsGarbage` vs `SavePackage` — When Each Is Required

**What:** Test assets created in automation tests have two different lifecycle needs. Using the wrong approach causes either memory leaks (no `MarkAsGarbage`) or broken subsequent tests that try to reload the asset (no `SavePackage`).

**Wrong pattern (missing cleanup or persistence):**
```cpp
// WRONG — no cleanup: asset stays in memory, leaks between tests
UBlueprint* TestBP = FKismetEditorUtilities::CreateBlueprint(...);
// ... run assertions ...
return true; // leaked

// ALSO WRONG — MarkAsGarbage without SavePackage:
// if a later test calls LoadObject on this path, it gets a stale package warning
TestBP->MarkAsGarbage(); // cleaned from memory but package still registered as "dirty"
```

**Correct pattern:**
```cpp
// If the test only needs the asset IN THIS TEST (transient use):
// → Create in GetTransientPackage(), call MarkAsGarbage at end, no SavePackage needed
UBlueprint* TestBP = FKismetEditorUtilities::CreateBlueprint(
    ParentClass,
    GetTransientPackage(),  // Transient — never on disk
    FName(TEXT("BP_TestTemp")),
    ...);
// ... assertions ...
TestBP->MarkAsGarbage(); // Required — prevents leak across tests
return true;

// If a LATER TEST needs to LoadObject on this asset's path:
// → Create in a real package, SavePackage immediately, MarkAsGarbage at end
UPackage* Pkg = CreatePackage(TEXT("/Game/Tests/BP_Persistent"));
UBlueprint* TestBP = FKismetEditorUtilities::CreateBlueprint(ParentClass, Pkg, ...);

FString FilePath = FPackageName::LongPackageNameToFilename(
    TEXT("/Game/Tests/BP_Persistent"), FPackageName::GetAssetPackageExtension());
FSavePackageArgs SaveArgs;
SaveArgs.TopLevelFlags = RF_Standalone; // RF_Standalone is sufficient; Blueprint UObject already has RF_Public set by CreateBlueprint
UPackage::SavePackage(Pkg, TestBP, *FilePath, SaveArgs); // Persist to disk

// ... assertions ...
TestBP->MarkAsGarbage(); // Still required to clean up memory
return true;
```

**Rule of thumb:**
- `GetTransientPackage()` + `MarkAsGarbage()` → for single-test assets
- Named package + `SavePackage()` + `MarkAsGarbage()` → for assets referenced by later tests or MCP tools

**Why:** `MarkAsGarbage()` removes the object from GC roots so the engine can collect it. Without it, the asset stays alive across tests. `SavePackage()` is separate — it writes the package to disk so `LoadObject` (called by MCP tools in E2E tests) can find it without the dreaded `SkipPackage` warning.

**Source:** `Plugins/UnrealCortex/Source/CortexBlueprint/Private/Operations/CortexBPAssetOps.cpp` (lines 594, 918); `Plugins/UnrealCortex/Source/CortexBlueprint/Private/Tests/CortexBPContentSetupTest.cpp`

---

## Asset Loading

### Recipe 4: `LoadObject` Guard Pattern — Preventing SkipPackage Warnings

**What:** Calling `LoadObject` on a path that doesn't exist generates a "SkipPackage" log warning that pollutes test output and can mask real errors. Always guard `LoadObject` with a package existence check.

**Wrong pattern:**
```cpp
// WRONG — if /Game/Test/BP_Missing doesn't exist, generates:
// LogLinker: Warning: SkipPackage: /Game/Test/BP_Missing
UBlueprint* BP = LoadObject<UBlueprint>(nullptr, TEXT("/Game/Test/BP_Missing"));
if (!BP) { return error; } // Too late — warning already printed
```

**Correct pattern:**
```cpp
// CORRECT — guard with package existence check
FString AssetPath = TEXT("/Game/Test/BP_Missing");
FString PkgName = FPackageName::ObjectPathToPackageName(AssetPath);

if (!FindPackage(nullptr, *PkgName) && !FPackageName::DoesPackageExist(PkgName))
{
    // Asset doesn't exist — return error without generating any log warning
    return FCortexCommandResult::Error(TEXT("AssetNotFound"),
        FString::Printf(TEXT("Asset not found: %s"), *AssetPath));
}

UBlueprint* BP = LoadObject<UBlueprint>(nullptr, *AssetPath);
```

**Required include:**
```cpp
#include "Misc/PackageName.h"  // FPackageName::ObjectPathToPackageName, DoesPackageExist
```

**Why:** `FPackageName::DoesPackageExist()` checks the file system without loading anything. `FindPackage()` checks if the package is already in memory. Together they cover all cases where the asset is accessible without triggering the linker's SkipPackage warning path.

**Source:** Pattern documented in `CLAUDE.md` Critical Gotchas; helper implementation in multiple `*Ops.cpp` files.

---

## Transactions

### Recipe 5: `FScopedTransaction` Placement — Before Modification, Not Around the Function

**What:** `FScopedTransaction` must be created before any object modification, not around the entire function. The transaction captures the undo snapshot at the point of creation — objects modified before the transaction was opened are not included.

**Wrong pattern:**
```cpp
// WRONG — transaction created AFTER modifications are already made
// Modify() calls below are NOT captured — they happen before FScopedTransaction opens the undo record
void FMyOps::RenameNode(UEdGraph* Graph, UEdGraphNode* Node, const FString& NewName)
{
    Node->NodeComment = NewName;                  // Modified BEFORE transaction — NOT undoable
    Graph->Modify();                              // Modify() has nowhere to write; no open record yet

    FScopedTransaction Transaction(              // Created after modifications — too late
        FText::FromString(TEXT("Rename Node")));
    Node->ReconstructNode();
}
```

**Correct pattern:**
```cpp
// CORRECT — transaction created BEFORE any modification
void FMyOps::RenameNode(UEdGraph* Graph, UEdGraphNode* Node, const FString& NewName)
{
    FScopedTransaction Transaction(              // Created FIRST
        FText::FromString(
            FString::Printf(TEXT("Cortex: Rename Node %s"), *Node->GetNodeTitle(ENodeTitleType::FullTitle).ToString())));

    Graph->Modify();                             // Now inside transaction scope
    Node->Modify();                              // Register for undo
    Node->NodeComment = NewName;                 // Modification is captured
    Node->ReconstructNode();
}
```

**Format for Cortex tools:**
```cpp
// ActionName and TargetName are FString variables from the calling context
// e.g., ActionName = TEXT("Rename Node"), TargetName = Node->GetName()
FScopedTransaction Transaction(
    FText::FromString(
        FString::Printf(TEXT("Cortex: %s %s"), *ActionName, *TargetName)));
```

**Why:** `FScopedTransaction` opens an undo record in the global undo buffer. Explicit `Modify()` calls on each UObject then snapshot that object's pre-change state into the open record. Without an open transaction, `Modify()` is a no-op for undo purposes. Without `Modify()` inside a transaction, the snapshot is never written. Call `Modify()` on **every** object whose properties will change — not just the outermost container. A missing `Modify()` on a nested object produces a silent partial undo where some changes revert and others don't. The transaction is committed (or rolled back) when it goes out of scope.

**Source:** `Plugins/UnrealCortex/Source/CortexBlueprint/Private/Operations/CortexBPGraphOps.cpp`

---

## Reflection

### Recipe 6: `FArrayProperty` + `FScriptArrayHelper` — Accessing Array Properties via Reflection

**What:** Accessing `TArray<T>` properties on a UObject via the reflection system requires `FArrayProperty` + `FScriptArrayHelper`. Direct casting or indexing the raw property pointer crashes.

**Wrong pattern (AI commonly generates direct cast):**
```cpp
// WRONG — ContainerPtrToValuePtr gives you the raw array storage, but without
// FScriptArrayHelper you have no way to know element size, count, or layout.
// Indexing this void* as a flat array is undefined behavior.
FProperty* Prop = Object->GetClass()->FindPropertyByName(FName(TEXT("MyArray")));
void* ArrayData = Prop->ContainerPtrToValuePtr<void>(Object); // Gets raw storage — this part is fine
// Crash: cannot safely index ArrayData without knowing element stride/count
```

**Correct pattern:**
```cpp
// CORRECT — use FArrayProperty + FScriptArrayHelper
FProperty* Prop = Object->GetClass()->FindPropertyByName(FName(TEXT("MyArray")));
FArrayProperty* ArrayProp = CastField<FArrayProperty>(Prop);
if (!ArrayProp)
{
    return; // Not an array property
}

FScriptArrayHelper Helper(ArrayProp, ArrayProp->ContainerPtrToValuePtr<void>(Object));
FProperty* InnerProp = ArrayProp->Inner; // The element type

for (int32 i = 0; i < Helper.Num(); ++i)
{
    void* ElementPtr = Helper.GetRawPtr(i);

    // Read element based on inner type
    if (FObjectProperty* ObjProp = CastField<FObjectProperty>(InnerProp))
    {
        UObject* Element = ObjProp->GetObjectPropertyValue(ElementPtr);
        // use Element
    }
    else if (FStructProperty* StructProp = CastField<FStructProperty>(InnerProp))
    {
        // use StructProp->Struct to get field info, ElementPtr for data
    }
}
```

**Required include:**
```cpp
#include "UObject/UnrealType.h"    // FProperty, FArrayProperty, FObjectProperty
#include "UObject/PropertyAccessUtil.h" // Optional utilities
```

**Why:** `TArray<T>` is not a plain C++ array — it's a heap-allocated buffer with a separate count and capacity. `FScriptArrayHelper` knows how to interpret the raw buffer using the `FArrayProperty` metadata (element size, alignment). Without it, all array access is undefined behavior.

**Source:** `Plugins/UnrealCortex/Source/CortexBlueprint/Private/Operations/CortexBPAnalysisOps.cpp` (line 682); `Plugins/UnrealCortex/Source/CortexData/Private/Operations/CortexDataTableOps.cpp` (line 68)

---

## Contributing Recipes

Add a recipe when a plan or implementation uses a wrong UE API pattern. Keep this battle-tested, not speculative.

**Template:**

```markdown
### Recipe N: `API::Name` — Short Description

**What:** One sentence — what operation this covers and why it's tricky.

**Wrong pattern (AI commonly generates X):**
```cpp
// WRONG — explain why this fails (silent wrong behavior / crash / link error)
<wrong code>
```

**Correct pattern:**
```cpp
// CORRECT — verified working
<correct code>
```

**Why:** Causal explanation of the UE internals that make the wrong pattern fail.

**Source:** `Plugins/UnrealCortex/Source/...` (line N or function name)
```

**When to add a recipe:**
- A code review catches an AI-generated wrong pattern in a PR → add recipe before merging
- A test fails due to an API misuse → add recipe as part of the fix commit
- A plan review catches a wrong pattern during planning → add recipe as part of the session
