# build.ps1 — Windows PowerShell build script for beam_core (Rust/PyO3 extension)
# Compiles the Rust crate via maturin + uv and produces a .pyd in this directory.
#
# Prerequisites: Rust (https://rustup.rs/), uv (https://docs.astral.sh/uv/)
# Usage: .\build.ps1          (release)
#        .\build.ps1 debug    (debug build)

param(
    [ValidateSet("release", "debug")]
    [string]$Mode = "release"
)

$ErrorActionPreference = "Stop"
Push-Location $PSScriptRoot

# Ensure Rust's cargo is on PATH (standard Windows install location)
if (Test-Path "$env:USERPROFILE\.cargo\bin") {
    $env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"
}

try {
    # --- Check prerequisites ---
    $cargo = Get-Command cargo -ErrorAction SilentlyContinue
    if (-not $cargo) {
        Write-Host "ERROR: cargo not found. Install Rust from https://rustup.rs/" -ForegroundColor Red
        exit 1
    }
    Write-Host "[*] cargo $(& cargo --version)" -ForegroundColor Cyan

    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if (-not $uv) {
        Write-Host "ERROR: uv not found. Install from https://docs.astral.sh/uv/" -ForegroundColor Red
        exit 1
    }
    Write-Host "[*] uv $(& uv --version)" -ForegroundColor Cyan

    # --- Remove stale Linux .so if present ---
    $staleSo = Get-ChildItem -Filter "*.so" -ErrorAction SilentlyContinue
    if ($staleSo) {
        Write-Host "[*] Removing stale .so file(s): $($staleSo.Name -join ', ')" -ForegroundColor Yellow
        $staleSo | Remove-Item -Force
    }

    # --- Build via maturin (uses uv for ephemeral maturin + Python env) ---
    $maturinArgs = if ($Mode -eq "debug") { @("develop") } else { @("develop", "--release") }
    Write-Host "[*] Running: uv run --with maturin maturin $($maturinArgs -join ' ')" -ForegroundColor Cyan

    uv run --with maturin maturin @maturinArgs
    if ($LASTEXITCODE -ne 0) {
        throw "maturin develop failed"
    }

    # maturin places the .dll in target/<mode>/ — copy it to .pyd here
    $targetDir = if ($Mode -eq "debug") { "target\debug" } else { "target\release" }
    $dllPath = Join-Path $targetDir "beam_core.dll"
    if (-not (Test-Path $dllPath)) {
        throw "Built DLL not found at: $dllPath"
    }

    $pySuffix = uv run python -c "import importlib.machinery; print(importlib.machinery.EXTENSION_SUFFIXES[0])"
    $pySuffix = $pySuffix.Trim()
    $outPath = "beam_core$pySuffix"

    Write-Host "[*] Copying $dllPath -> $outPath" -ForegroundColor Cyan
    Copy-Item -Path $dllPath -Destination $outPath -Force

    # --- Verify ---
    Write-Host "[*] Verifying import..." -ForegroundColor Cyan
    $verifyCode = @"
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))
import beam_core
assert beam_core.score_pos_py is not None
assert beam_core.beam_search_py is not None
assert beam_core.max_gap_move_py is not None
assert beam_core.multi_beam_py is not None
print('beam_core: all 4 functions OK')
"@
    uv run python -c $verifyCode
    if ($LASTEXITCODE -ne 0) {
        throw "Import verification failed"
    }

    Write-Host "`n[OK] beam_core built and verified! ($Mode)" -ForegroundColor Green
}
finally {
    Pop-Location
}
