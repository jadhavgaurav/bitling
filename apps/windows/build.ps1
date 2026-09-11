#!/usr/bin/env pwsh
# Builds Bitling.exe from source and (optionally) installs it.
#   .\build.ps1                        -> build and install to $env:LOCALAPPDATA\Programs\Bitling
#   .\build.ps1 -Dest 'C:\Apps\Bitling' -> build and install somewhere else
#   .\build.ps1 -NoInstall             -> build only (result in publish\)
#   .\build.ps1 -Runtime win-arm64     -> target a different RID (default win-x64)
#
# Mirrors apps/macos/build.sh's shape as closely as .NET's own tooling allows: there is no
# universal-binary equivalent, so this publishes one self-contained, single-file exe for
# the chosen RID rather than lipo-merging two architectures.
#
# THIS SCRIPT HAS NOT BEEN RUN. It was written by reading build.sh and the .NET SDK docs,
# on a machine with no Windows or .NET desktop toolchain available to verify it against.
# Expect to debug it on first use.
param(
    [string]$Dest = (Join-Path $env:LOCALAPPDATA "Programs\Bitling"),
    [string]$Runtime = "win-x64",
    [switch]$NoInstall
)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Project = Join-Path $PSScriptRoot "Bitling.Windows\Bitling.Windows.csproj"
$ResourcesDir = Join-Path $PSScriptRoot "Bitling.Windows\Resources"
$WebSource = Join-Path $RepoRoot "apps\macos\web\bitling.html"

function Get-PythonCommand {
    foreach ($candidate in @("python3", "python")) {
        if (Get-Command $candidate -ErrorAction SilentlyContinue) { return $candidate }
    }
    throw "python3 (or python) is required to derive pet.html from the shared web source"
}

Write-Host "-> deriving desktop page from $WebSource"
New-Item -ItemType Directory -Force -Path $ResourcesDir | Out-Null
$python = Get-PythonCommand
& $python (Join-Path $RepoRoot "packages\pet-engine\scripts\make_pet_html.py") $WebSource (Join-Path $ResourcesDir "pet.html")
if ($LASTEXITCODE -ne 0) { throw "make_pet_html.py failed" }

Copy-Item (Join-Path $RepoRoot "apps\macos\web\panel.html") (Join-Path $ResourcesDir "panel.html") -Force
Copy-Item (Join-Path $RepoRoot "apps\macos\Resources\avatars") $ResourcesDir -Recurse -Force
Copy-Item (Join-Path $RepoRoot "apps\macos\Resources\pets") $ResourcesDir -Recurse -Force

# TODO: generate Resources\Bitling.ico. apps/macos/tools/makeicon.swift draws the icon with
# Cocoa and can't run here; until a Windows-side icon generator exists, the app falls back
# to the default system icon (see AppController.LoadTrayIcon).

Write-Host "-> publishing self-contained single-file exe ($Runtime)"
dotnet publish $Project `
    -c Release `
    -r $Runtime `
    --self-contained true `
    -p:PublishSingleFile=true `
    -p:IncludeNativeLibrariesForSelfExtract=true `
    -o (Join-Path $PSScriptRoot "publish")
if ($LASTEXITCODE -ne 0) { throw "dotnet publish failed" }

if ($NoInstall) {
    Write-Host "built $(Join-Path $PSScriptRoot 'publish\Bitling.exe')"
    exit 0
}

Write-Host "-> installing to $Dest"
$running = Get-Process -Name "Bitling" -ErrorAction SilentlyContinue
if ($running) { $running | Stop-Process -Force; Start-Sleep -Seconds 1 }
New-Item -ItemType Directory -Force -Path $Dest | Out-Null
Copy-Item (Join-Path $PSScriptRoot "publish\*") $Dest -Recurse -Force
Write-Host "installed $Dest\Bitling.exe"
Write-Host "run it once, then add a Start Menu / taskbar shortcut by hand if you want one"
Write-Host "the bitling CLI lives at $Dest\bitling.ps1 - add $Dest to PATH to call it as `"bitling.ps1`" from anywhere, or wrap it in a `"bitling.cmd`" shim"
