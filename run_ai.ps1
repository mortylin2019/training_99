$ErrorActionPreference = "Stop"
Write-Host "Activating .venv..."
& ".\.venv\Scripts\Activate.ps1"
Write-Host "Launching AI Controller..."
python hijack_tools/game_control.py
