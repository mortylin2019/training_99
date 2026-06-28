$ErrorActionPreference = "Stop"
Write-Host "Activating .venv..."
& ".\.venv\Scripts\Activate.ps1"
Write-Host "Launching AI Runner..."
python hijack_tools/runner.py
