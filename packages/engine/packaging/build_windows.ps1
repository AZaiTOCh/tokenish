$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..
.\.venv\Scripts\pip install -e ".[dev]"
.\.venv\Scripts\pyinstaller packaging\tokenish.spec --noconfirm
Write-Host "exe at dist\tokenish\tokenish.exe"
