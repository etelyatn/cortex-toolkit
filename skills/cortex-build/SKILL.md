---
name: cortex-build
description: Use when building the Unreal Engine project, after modifying C++ source files, or when build errors need diagnosis
---

# Cortex Build

Builds the UE project with proper configuration.

## Steps

### 1. Read Configuration

Read the effective Cortex config to get the engine path:
1. Start with `.cortex/config.yaml`
2. If present, merge `.cortex/config.local.yaml` over it for per-machine overrides
3. Fall back to `$UE_PATH` only when project config does not provide `engine.path`

Use the shared loader when available:
```bash
python cortex-toolkit/lib/cortex_config.py --project-dir . --get engine.path
```

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
