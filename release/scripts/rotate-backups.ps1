param(
    [string]$BackupDir = "release/backups",
    [int]$Keep = 10
)

$ErrorActionPreference = "Stop"

if ($Keep -lt 1) {
    throw "Keep must be at least 1."
}

if (-not (Test-Path $BackupDir)) {
    Write-Host "Backup directory does not exist: $BackupDir"
    exit 0
}

$backups = Get-ChildItem `
    -Path $BackupDir `
    -Filter "*.dump" `
    -File |
    Sort-Object LastWriteTime -Descending

if ($backups.Count -le $Keep) {
    Write-Host "No backup rotation needed. Found $($backups.Count), keeping $Keep."
    exit 0
}

$toDelete = $backups | Select-Object -Skip $Keep

foreach ($backup in $toDelete) {
    Write-Host "Deleting old backup: $($backup.FullName)"
    Remove-Item -LiteralPath $backup.FullName
}

Write-Host "Backup rotation complete. Kept $Keep backup(s)."