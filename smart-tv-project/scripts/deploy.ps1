# Packages app/ into dist/, installs it on the TV in Dev Mode, and opens it.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File scripts\deploy.ps1
$ErrorActionPreference = 'Stop'
$tools = Join-Path $env:USERPROFILE '.lgtv\tools'
$env:Path = "$tools\node;$tools\cli\node_modules\.bin;$env:Path"
$root = Split-Path -Parent $PSScriptRoot
$dist = Join-Path $root 'dist'
$device = 'lgtv'

New-Item -ItemType Directory -Force -Path $dist | Out-Null
Get-ChildItem $dist -Filter *.ipk | Remove-Item -Force
ares-package --no-minify --outdir $dist (Join-Path $root 'app')
if ($LASTEXITCODE -ne 0) { throw 'Packaging failed' }
$ipk = (Get-ChildItem $dist -Filter *.ipk | Select-Object -First 1).FullName
Write-Host "Package: $ipk ($([math]::Round((Get-Item $ipk).Length / 1KB, 1)) KB)"

ares-install --device $device $ipk
if ($LASTEXITCODE -ne 0) { throw 'Install failed' }
ares-launch --device $device com.local.lgdashboard
if ($LASTEXITCODE -ne 0) { throw 'Launch failed' }
