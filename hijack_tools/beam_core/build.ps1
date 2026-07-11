# build.ps1 — Windows PowerShell build script for beam_core (Rust/PyO3 extension)
# Builds natively with MSVC via cargo, copies .dll → .pyd. No maturin/venv pollution.
#
# Prerequisites: Rust MSVC (https://rustup.rs/), uv (https://docs.astral.sh/uv/)
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
    Write-Host "[*] toolchain: $(& rustup show active-toolchain)" -ForegroundColor Cyan

    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if (-not $uv) {
        Write-Host "ERROR: uv not found. Install from https://docs.astral.sh/uv/" -ForegroundColor Red
        exit 1
    }

    # --- Clean stale files ---
    Get-ChildItem -Filter "*.so" -ErrorAction SilentlyContinue | Remove-Item -Force
    Get-ChildItem -Filter "beam_core.cp*-win_amd64.pyd" -ErrorAction SilentlyContinue | Remove-Item -Force
    if (Test-Path ".venv") {
        Write-Host "[*] Removing stale .venv..." -ForegroundColor Yellow
        Remove-Item ".venv" -Recurse -Force
    }

    # --- Build natively with cargo (NOT maturin develop — avoids venv pollution) ---
    Write-Host "[*] Building with cargo ($Mode)..." -ForegroundColor Cyan
    if ($Mode -eq "debug") {
        cargo build
    } else {
        cargo build --release
    }
    if ($LASTEXITCODE -ne 0) {
        throw "cargo build failed"
    }

    # --- Copy .dll → .pyd ---
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
    & {
        Set-Location $PSScriptRoot
        uv run python -c @"
import sys; sys.path.insert(0, '.')
import beam_core
assert beam_core.score_pos_py is not None
assert beam_core.beam_search_py is not None
assert beam_core.max_gap_move_py is not None
assert beam_core.multi_beam_py is not None
print('beam_core: all 4 functions OK')
"@
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Import verification failed"
    }

    Write-Host "`n[OK] beam_core built and verified! ($Mode)" -ForegroundColor Green
    Write-Host "[!] Run with: uv run python hijack_tools/runner.py --ai ai_beam" -ForegroundColor Cyan
}
finally {
    Pop-Location
}
