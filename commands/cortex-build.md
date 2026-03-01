---
name: cortex-build
description: Use when building the Unreal Engine project, after modifying C++ source files, or when build errors need diagnosis
---

# Cortex Build

Builds the UE project with proper configuration.

## Steps

### 1. Read Configuration

Read `.cortex/config.yaml` to get the engine path. Fall back to `$UE_56_PATH` env var.

Find the `.uproject` file in the project root.

### 2. Run Build

Execute the build command:
```bash
"$ENGINE_PATH/Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.exe" \
  <ProjectName>Editor Win64 Development \
  -Project="<absolute path to .uproject>" \
  -WaitMutex -FromMsBuild
```

### 3. Handle Results

**Success:** Report "Build succeeded" with any warnings.

**Failure:** Parse the build output:
- Extract error messages (lines containing `error C` or `error :`)
- Identify the failing file and line number
- Suggest fixes based on common patterns

**DLL locked:** If build fails with DLL lock error, suggest:
1. Close UE Editor
2. Delete `Intermediate/Build/BuildRules/*.dll`
3. Rebuild

### 4. Post-Build

If UE Editor is running, it will hot-reload automatically. No action needed.
