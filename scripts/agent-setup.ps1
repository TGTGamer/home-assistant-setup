# ------------------------------------------------------------------------------
# File: scripts/agent-setup.ps1
# Project: home-assistant-setup
# Last modified: 2026-09-25
#
# Copyright 2026 TGTGamer - All Rights Reserved
#
# Licensed under the Fair Core License, Version 1.0, MIT Future License
# (FCL-1.0-MIT); you may not use this file except in compliance with the
# License in the LICENSE file at the root of this repository. Each version
# becomes available under the MIT license on the second anniversary of the
# date it is made available.
#
# You must not move, change, disable, or circumvent any license key
# functionality in this software, or modify it to remove protected
# functionality.
#
# Contributions are made under the TGTGamer Cooperation Commitment in
# CONTRIBUTING.md, and everyone taking part follows CODE_OF_CONDUCT.md.
#
# DELETING THIS NOTICE AUTOMATICALLY VOIDS YOUR LICENSE
# ------------------------------------------------------------------------------

# Idempotent setup for people and agents on Windows: installs a pinned,
# checksum-verified uv if needed, syncs the locked Python environment, then
# runs the fast checks.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$UvVersion = "0.11.26"
# SHA-256 of each uv release archive, from the release's .sha256 files.
$UvSha256 = @{
    "x86_64-pc-windows-msvc"  = "4e1278ede866be6c0bf32d2f466cc6de7a9fb399ecf20c9ce2d186e52424be47"
    "aarch64-pc-windows-msvc" = "98246149741f558e25e45ecf2b0b20f34de0634269f2bf0dcb4012d4b6ba289a"
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    $Target = if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64") { "aarch64-pc-windows-msvc" } else { "x86_64-pc-windows-msvc" }
    $Archive = "uv-$Target.zip"
    $Temp = Join-Path ([System.IO.Path]::GetTempPath()) ([System.Guid]::NewGuid())
    New-Item -ItemType Directory -Path $Temp | Out-Null
    try {
        $Zip = Join-Path $Temp $Archive
        Invoke-WebRequest -Uri "https://github.com/astral-sh/uv/releases/download/$UvVersion/$Archive" -OutFile $Zip
        $Actual = (Get-FileHash -Algorithm SHA256 $Zip).Hash.ToLowerInvariant()
        if ($Actual -ne $UvSha256[$Target]) { throw "uv archive checksum mismatch ($Actual); not installing" }
        Expand-Archive -Path $Zip -DestinationPath $Temp
        $Bin = Join-Path $env:USERPROFILE ".local\bin"
        New-Item -ItemType Directory -Force -Path $Bin | Out-Null
        Copy-Item (Join-Path $Temp "uv.exe"), (Join-Path $Temp "uvx.exe") $Bin
        $env:Path = "$Bin;$env:Path"
    } finally {
        Remove-Item -Recurse -Force $Temp
    }
}
uv sync --locked
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
uv run pytest -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Output "agent-setup: ok"
