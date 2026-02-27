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
                $destination = Join-Path $targetRoot $_.Name
                if (Test-Path $destination) {
                    throw "Duplicate skill folder name detected: '$($_.Name)'. Skill names must be unique across domain plugins."
                }
                Copy-Item -Path $_.FullName -Destination $destination -Recurse -Force
            }
        }
    }

Write-Output "Unified skills refreshed at: $targetRoot"
