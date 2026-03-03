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

| BP Type | `ParentClass` | `BlueprintClass` | `GeneratedClassClass` |
|---------|--------------|------------------|-----------------------|
| Actor | `AActor` or subclass | `UBlueprint::StaticClass()` | `UBlueprintGeneratedClass::StaticClass()` |
| Widget | `UUserWidget` or subclass | `FindObject<UClass>(nullptr, TEXT("/Script/UMGEditor.WidgetBlueprint"))` | `UBlueprintGeneratedClass::StaticClass()` |
| Component | `UActorComponent` or subclass | `UBlueprint::StaticClass()` | `UBlueprintGeneratedClass::StaticClass()` |
| Interface | `UInterface` | `UBlueprint::StaticClass()` | `UBlueprintGeneratedClass::StaticClass()` |
| FunctionLibrary | `UBlueprintFunctionLibrary` | `UBlueprint::StaticClass()` | `UBlueprintGeneratedClass::StaticClass()` |

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

**Correct pattern:**
```cpp
// CORRECT — resolve at runtime, no compile-time dependency
// Cache the result in a static local to avoid repeated lookups
static UClass* WidgetBlueprintClass = nullptr;
if (!WidgetBlueprintClass)
{
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

**Common paths to resolve:**

| Class | Path |
|-------|------|
| `UWidgetBlueprint` | `/Script/UMGEditor.WidgetBlueprint` |
| `UUserWidget` | `/Script/UMG.UserWidget` |
| `UCommonActivatableWidget` | `/Script/CommonUI.CommonActivatableWidget` |
| `UGameplayAbility` | `/Script/GameplayAbilities.GameplayAbility` |

**Why:** `FindObject` searches the currently-loaded class pool at runtime. This works because UMGEditor is always loaded in the editor, where you'd use this class. In cooked builds, the editor module isn't present — but you'd never need `UWidgetBlueprint` at runtime anyway.

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
    TEXT("/Game/Tests/BP_Persistent"), FPackageSavingContext::GetPackageExtension(false));
FSavePackageArgs SaveArgs;
SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
UPackage::SavePackage(Pkg, TestBP, *FilePath, SaveArgs); // Persist to disk

// ... assertions ...
TestBP->MarkAsGarbage(); // Still required to clean up memory
return true;
```

**Rule of thumb:**
- `GetTransientPackage()` + `MarkAsGarbage()` → for single-test assets
- Named package + `SavePackage()` + `MarkAsGarbage()` → for assets referenced by later tests or MCP tools

**Why:** `MarkAsGarbage()` removes the object from GC roots so the engine can collect it. Without it, the asset stays alive across tests. `SavePackage()` is separate — it writes the package to disk so `LoadObject` (called by MCP tools in E2E tests) can find it without the dreaded `SkipPackage` warning.

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
void FMyOps::RenameNode(UEdGraph* Graph, UEdGraphNode* Node, const FString& NewName)
{
    Node->NodeComment = NewName;                  // Modified BEFORE transaction — NOT undoable
    Graph->Modify();                              // Too late

    FScopedTransaction Transaction(              // Created after modifications
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
FScopedTransaction Transaction(
    FText::FromString(
        FString::Printf(TEXT("Cortex: %s %s"), *ActionName, *TargetName)));
```

**Why:** `FScopedTransaction` works by calling `Modify()` on objects to save their pre-modification state into the undo buffer. Any modification that happens before the transaction was opened has no pre-state snapshot — it cannot be undone. The transaction is committed (or rolled back) when it goes out of scope.

---

## Reflection

### Recipe 6: `FArrayProperty` + `FScriptArrayHelper` — Accessing Array Properties via Reflection

**What:** Accessing `TArray<T>` properties on a UObject via the reflection system requires `FArrayProperty` + `FScriptArrayHelper`. Direct casting or indexing the raw property pointer crashes.

**Wrong pattern (AI commonly generates direct cast):**
```cpp
// WRONG — FProperty is not directly indexable
FProperty* Prop = Object->GetClass()->FindPropertyByName(FName(TEXT("MyArray")));
// Attempting to read array elements from raw pointer — undefined behavior
void* ArrayData = Prop->ContainerPtrToValuePtr<void>(Object);
// No way to safely iterate — crash
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
