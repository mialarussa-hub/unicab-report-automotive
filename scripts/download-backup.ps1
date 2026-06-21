# UNICAB — scarica l'ultimo backup dal server e verifica il checksum.
# Eseguito da Windows (PowerShell).
#
# Usage:
#   ./scripts/download-backup.ps1
#   ./scripts/download-backup.ps1 -DestDir "E:\Backups\UNICAB"

param(
  [string]$DestDir = "D:\PROGETTI\UNICAB\backups",
  [string]$Server  = "unicab@46.225.147.176",
  [int]   $Port    = 2222
)

$ErrorActionPreference = 'Stop'

New-Item -ItemType Directory -Force -Path $DestDir | Out-Null

Write-Host "Cerco l'ultimo backup su $Server..." -ForegroundColor Cyan
$latest = (ssh -p $Port $Server "ls -1t /opt/unicab/backups/unicab-*.tar.gz 2>/dev/null | head -1").Trim()
if (-not $latest) {
  throw "Nessun backup trovato sul server in /opt/unicab/backups/"
}
$filename = Split-Path $latest -Leaf
Write-Host "  Trovato: $filename" -ForegroundColor Green

$destFile = Join-Path $DestDir $filename
if (Test-Path $destFile) {
  Write-Host "  ⚠️  File già presente in locale: $destFile" -ForegroundColor Yellow
  $resp = Read-Host "  Sovrascrivere? [y/N]"
  if ($resp -ne 'y' -and $resp -ne 'Y') { Write-Host "Annullato."; exit 0 }
}

Write-Host "Download tarball..." -ForegroundColor Cyan
scp -P $Port "${Server}:${latest}" $destFile
if ($LASTEXITCODE -ne 0) { throw "scp del tarball fallito" }

Write-Host "Download checksum..." -ForegroundColor Cyan
scp -P $Port "${Server}:${latest}.sha256" "$destFile.sha256"
if ($LASTEXITCODE -ne 0) { throw "scp del checksum fallito" }

Write-Host "Verifica SHA256..." -ForegroundColor Cyan
$expected = (Get-Content "$destFile.sha256").Split(' ')[0].ToLower().Trim()
$actual   = (Get-FileHash $destFile -Algorithm SHA256).Hash.ToLower()
if ($expected -ne $actual) {
  Write-Host "  ❌ Checksum mismatch!" -ForegroundColor Red
  Write-Host "     atteso : $expected"
  Write-Host "     attuale: $actual"
  throw "Backup corrotto o trasferimento incompleto"
}
Write-Host "  ✅ Checksum OK" -ForegroundColor Green

$sizeMB = [math]::Round((Get-Item $destFile).Length / 1MB, 1)
Write-Host ""
Write-Host "✅ Backup salvato:" -ForegroundColor Green
Write-Host "   $destFile  ($sizeMB MB)"
Write-Host ""
Write-Host "Prossimi step consigliati:" -ForegroundColor Cyan
Write-Host "  1. Copiare il file anche su un secondo supporto (Drive / NAS / HDD esterno)"
Write-Host "  2. Aprire MANIFEST.txt con:  tar -tzf `"$destFile`" | findstr MANIFEST"
Write-Host "  3. Procedere alla pulizia del server (vedi pm/ops/BACKUP-RESTORE.md)"
