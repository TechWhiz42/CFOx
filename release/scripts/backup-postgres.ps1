param(
    [string]$ComposeFile = "docker-compose.production.yml",
    [string]$EnvFile = ".env.production",
    [string]$OutputDir = "release/backups"
)

$ErrorActionPreference = "Stop"

function Read-DotEnvValue {
    param(
        [string]$Path,
        [string]$Name
    )

    $line = Get-Content $Path |
        Where-Object {
            $_ -match "^\s*$Name\s*="
        } |
        Select-Object -First 1

    if (-not $line) {
        return $null
    }

    return ($line -replace "^\s*$Name\s*=", "").Trim().Trim('"').Trim("'")
}

if (-not (Test-Path $EnvFile)) {
    throw "Environment file does not exist: $EnvFile"
}

$postgresUser = Read-DotEnvValue -Path $EnvFile -Name "POSTGRES_USER"
$postgresDb = Read-DotEnvValue -Path $EnvFile -Name "POSTGRES_DB"

if (-not $postgresUser) {
    throw "POSTGRES_USER is missing from $EnvFile"
}

if (-not $postgresDb) {
    throw "POSTGRES_DB is missing from $EnvFile"
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupName = "cfox-postgres-$timestamp.dump"
$backupPath = Join-Path $OutputDir $backupName

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

Write-Host "Creating PostgreSQL backup..."
Write-Host "Database: $postgresDb"
Write-Host "User: $postgresUser"
Write-Host "Output: $backupPath"

docker compose `
    -f $ComposeFile `
    --env-file $EnvFile `
    exec -T db `
    pg_dump `
    -U $postgresUser `
    -d $postgresDb `
    -Fc `
    -f /tmp/cfox-backup.dump

docker compose `
    -f $ComposeFile `
    --env-file $EnvFile `
    cp `
    db:/tmp/cfox-backup.dump `
    $backupPath

docker compose `
    -f $ComposeFile `
    --env-file $EnvFile `
    exec -T db `
    rm -f /tmp/cfox-backup.dump

if (-not (Test-Path $backupPath)) {
    throw "Backup file was not created."
}

if ((Get-Item $backupPath).Length -le 0) {
    throw "Backup file is empty."
}

Write-Host "Backup complete: $backupPath"