$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Install Git for Windows first. See README.md.' }
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) { throw 'Install Ollama for Windows first. See README.md.' }
$dataDir = Join-Path $env:LOCALAPPDATA 'OpenJarvis'
$toolsDir = Join-Path $dataDir 'tools\uv-0.13.6'
$uvExe = Join-Path $toolsDir 'uv.exe'
if (-not (Test-Path -LiteralPath $uvExe)) {
    New-Item -ItemType Directory -Force -Path $toolsDir | Out-Null
    $archive = Join-Path $toolsDir 'uv.zip'
    Write-Host 'Getting the Python setup tool...'
    Invoke-WebRequest 'https://github.com/astral-sh/uv/releases/download/0.13.6/uv-x86_64-pc-windows-msvc.zip' -OutFile $archive
    $expected = 'a2a8820d5eea32f08ef467ef3b7f66883a9b076d5737a2fc2fbb5f458d1bb50f'
    if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) { throw 'The setup tool download failed its file check.' }
    Expand-Archive -LiteralPath $archive -DestinationPath $toolsDir -Force
}
Write-Host 'Setting up Python 3.12 and Jarvis...'
$pythonExe = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    & $uvExe venv --python 3.12 .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python setup failed.' }
}
& $uvExe pip install --python $pythonExe -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency setup failed.' }
$env:HF_HOME = Join-Path $dataDir 'models'
Write-Host 'Getting the local speech recognition model...'
& $pythonExe (Join-Path $PSScriptRoot 'setup_runtime.py')
if ($LASTEXITCODE -ne 0) { throw 'Speech model download failed.' }
& $pythonExe (Join-Path $PSScriptRoot 'setup_wake.py')
if ($LASTEXITCODE -ne 0) { throw 'Wake model download failed.' }
Write-Host 'Getting the default local AI model. This can take a while...'
try { $null=Invoke-RestMethod 'http://127.0.0.1:11434/api/tags' -TimeoutSec 2 } catch {
    Start-Process -FilePath (Get-Command ollama).Source -ArgumentList 'serve' -WindowStyle Hidden
    Start-Sleep -Seconds 3
}
& ollama pull qwen2.5:7b-instruct-q4_K_M
if ($LASTEXITCODE -ne 0) { throw 'Ollama model download failed. Open Ollama, then run setup again.' }
Write-Host 'Free local voice is ready. ElevenLabs is optional; use Set-Voice-Key.ps1 if wanted.'
$shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'Start Jarvis.lnk'))
$shortcut.TargetPath = Join-Path $PSScriptRoot 'Start Jarvis.cmd'
$shortcut.WorkingDirectory = $PSScriptRoot
$shortcut.Save()
$voiceShortcut = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'Jarvis Vocals.lnk'))
$voiceShortcut.TargetPath = Join-Path $PSScriptRoot 'Start Vocals.cmd'
$voiceShortcut.WorkingDirectory = $PSScriptRoot
$voiceShortcut.Save()
Write-Host 'Ready. Open Start Jarvis on the Desktop. Follow the sign-in steps.'
