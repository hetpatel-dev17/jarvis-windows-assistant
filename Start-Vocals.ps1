$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'Start-Jarvis.ps1') -NoBrowser
$projectDir = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$pythonExe = Join-Path $PSScriptRoot '.venv\Scripts\pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    $pythonExe = Join-Path $projectDir 'work\OpenJarvis-main\.venv\Scripts\pythonw.exe'
}
Start-Process -FilePath $pythonExe -ArgumentList ('"'+(Join-Path $PSScriptRoot 'vocals_panel.py')+'"') -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
