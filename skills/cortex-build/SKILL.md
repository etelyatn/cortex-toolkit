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

Configure the bundled .NET environment (UE 5.8+ bundles .NET 10; UE 5.6/5.7 bundles .NET 8) and execute the build command:

**Bash / Git Bash:**
```bash
if [ -d "$ENGINE_PATH/Engine/Binaries/ThirdParty/DotNet/10.0/win-x64" ]; then
  export DOTNET_ROOT="$ENGINE_PATH/Engine/Binaries/ThirdParty/DotNet/10.0/win-x64"
elif [ -d "$ENGINE_PATH/Engine/Binaries/ThirdParty/DotNet/8.0/win-x64" ]; then
  export DOTNET_ROOT="$ENGINE_PATH/Engine/Binaries/ThirdParty/DotNet/8.0/win-x64"
fi
export DOTNET_MULTILEVEL_LOOKUP=0
export DOTNET_ROLL_FORWARD=LatestMajor

"$ENGINE_PATH/Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.exe" \
  <ProjectName>Editor Win64 Development \
  -Project="<absolute path to .uproject>" \
  -WaitMutex -FromMsBuild
```

**PowerShell (pwsh):**
```powershell
$dotnet10 = "$ENGINE_PATH/Engine/Binaries/ThirdParty/DotNet/10.0/win-x64"
$dotnet8 = "$ENGINE_PATH/Engine/Binaries/ThirdParty/DotNet/8.0/win-x64"
if (Test-Path $dotnet10) { $env:DOTNET_ROOT = $dotnet10 }
elseif (Test-Path $dotnet8) { $env:DOTNET_ROOT = $dotnet8 }
$env:DOTNET_MULTILEVEL_LOOKUP = "0"
$env:DOTNET_ROLL_FORWARD = "LatestMajor"

& "$ENGINE_PATH/Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.exe" `
  <ProjectName>Editor Win64 Development `
  -Project="<absolute path to .uproject>" `
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
