param(
    [string]$ToolkitRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"

$targetRoot = Join-Path $ToolkitRoot "skills"
New-Item -ItemType Directory -Force -Path $targetRoot | Out-Null

# Rebuild unified skills directory from domain plugin skill folders.
Get-ChildItem -Path $targetRoot -Directory -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force

Get-ChildItem -Path $ToolkitRoot -Directory |
    Where-Object { $_.Name -like "cortex-*" } |
    ForEach-Object {
        $skillsPath = Join-Path $_.FullName "skills"
        if (Test-Path $skillsPath) {
            Get-ChildItem -Path $skillsPath -Directory | ForEach-Object {
                Copy-Item -Path $_.FullName -Destination (Join-Path $targetRoot $_.Name) -Recurse -Force
            }
        }
    }

Write-Output "Unified skills refreshed at: $targetRoot"
