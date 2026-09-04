param(
    [Parameter(Mandatory = $true)]
    [string]$BackupPath,

    [string]$ComposeFile = "docker-compose.production.yml",
    [string]$EnvFile = ".env.production"
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

if (-not (Test-Path $BackupPath)) {
    throw "Backup file does not exist: $BackupPath"
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

Write-Host "WARNING: This will restore PostgreSQL from:"
Write-Host $BackupPath
Write-Host ""
Write-Host "Database: $postgresDb"
Write-Host "User: $postgresUser"
Write-Host ""
Write-Host "Press Ctrl+C to cancel, or Enter to continue."
Read-Host | Out-Null

docker compose `
    -f $ComposeFile `
    --env-file $EnvFile `
    cp `
    $BackupPath `
    db:/tmp/cfox-restore.dump

docker compose `
    -f $ComposeFile `
    --env-file $EnvFile `
    exec -T db `
    pg_restore `
    -U $postgresUser `
    -d $postgresDb `
    --clean `
    --if-exists `
    /tmp/cfox-restore.dump

docker compose `
    -f $ComposeFile `
    --env-file $EnvFile `
    exec -T db `
    rm -f /tmp/cfox-restore.dump

Write-Host "Restore complete."