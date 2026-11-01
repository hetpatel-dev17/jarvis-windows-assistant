$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Security
$dataDir = Join-Path $env:LOCALAPPDATA 'OpenJarvis\secrets'
New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
$keyPath = Join-Path $dataDir 'elevenlabs.dpapi'
if (Test-Path -LiteralPath $keyPath) {
    Write-Host 'An encrypted voice key already exists. Keeping it.'
    exit 0
}
$secureKey = Read-Host 'Paste your ElevenLabs API key, then press Enter' -AsSecureString
$pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
$raw = $null
try {
    $plainKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer).Trim()
    if ([string]::IsNullOrWhiteSpace($plainKey)) { throw 'No key was entered.' }
    $raw = [Text.Encoding]::Unicode.GetBytes($plainKey)
    $encrypted = [Security.Cryptography.ProtectedData]::Protect($raw,$null,[Security.Cryptography.DataProtectionScope]::CurrentUser)
    $hex = ([BitConverter]::ToString($encrypted)).Replace('-','').ToLowerInvariant()
    [IO.File]::WriteAllText($keyPath,$hex)
    Write-Host 'Voice key saved with Windows encryption.'
} finally {
    if ($raw) { [Array]::Clear($raw,0,$raw.Length) }
    $plainKey = $null
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
    $secureKey.Dispose()
}
