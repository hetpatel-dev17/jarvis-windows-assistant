param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$appDir = $PSScriptRoot
$projectDir = Split-Path (Split-Path $appDir -Parent) -Parent
$pythonExe = Join-Path $appDir '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    $pythonExe = Join-Path $projectDir 'work\OpenJarvis-main\.venv\Scripts\python.exe'
}
$dataDir = Join-Path $env:LOCALAPPDATA 'OpenJarvis'
New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
$env:OPENJARVIS_HOME = Join-Path $dataDir 'data'
$env:HF_HOME = Join-Path $dataDir 'models'
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $dataDir 'browsers'
$certFile = Join-Path $projectDir 'work\ca.pem'
if (Test-Path -LiteralPath $certFile) {
    $env:SSL_CERT_FILE = $certFile
    $env:REQUESTS_CA_BUNDLE = $certFile
}
function Show-SetupError([string]$message) {
    Add-Type -AssemblyName System.Windows.Forms
    [void][System.Windows.Forms.MessageBox]::Show($message,'Jarvis setup')
}
if (-not (Test-Path -LiteralPath $pythonExe)) {
    Show-SetupError 'Run Setup Windows.cmd in this folder first. Then open Start Jarvis.cmd.'
    exit 1
}
$ready = $false
try {
    $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8766/health' -TimeoutSec 2
    $ready = $health.app -eq 'personal-openjarvis'
} catch {}
if (-not $ready) {
    $ollamaReady = $false
    try { $null=Invoke-RestMethod 'http://127.0.0.1:11434/api/tags' -TimeoutSec 2; $ollamaReady=$true } catch {}
    if (-not $ollamaReady) {
        $ollamaCommand=Get-Command ollama.exe -ErrorAction SilentlyContinue
        if ($ollamaCommand) { Start-Process -FilePath $ollamaCommand.Source -ArgumentList 'serve' -WindowStyle Hidden }
    }
    $service = Start-Process -FilePath $pythonExe -ArgumentList ('"'+(Join-Path $appDir 'app.py')+'"') -WorkingDirectory $appDir -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $dataDir 'jarvis-output.log') -RedirectStandardError (Join-Path $dataDir 'jarvis-error.log')
    [System.IO.File]::WriteAllText((Join-Path $dataDir 'jarvis.pid'),[string]$service.Id)
    for ($attempt=0; $attempt -lt 45; $attempt++) {
        Start-Sleep -Seconds 1
        try { $health=Invoke-RestMethod 'http://127.0.0.1:8766/health' -TimeoutSec 2; if ($health.app -eq 'personal-openjarvis') {$ready=$true;break} } catch {}
        if ($service.HasExited) { break }
    }
}
if (-not $ready) {
    Show-SetupError ('Jarvis could not start. Return to the chat. Its error log is at '+(Join-Path $dataDir 'jarvis-error.log'))
    exit 1
}
$tokenPath=Join-Path $dataDir 'local-token.txt'
$localToken=[System.IO.File]::ReadAllText($tokenPath).Trim()
if (-not $NoBrowser) { Start-Process ('http://127.0.0.1:8766/#'+$localToken) }
$localToken=$null
