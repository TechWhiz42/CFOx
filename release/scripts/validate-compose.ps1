$ErrorActionPreference = "Stop"

$Root = "D:\CFOx"
$Compose = Join-Path $Root "docker-compose.production.yml"

if (-not (Test-Path $Compose)) {
    throw "Missing production compose file: $Compose"
}

docker compose -f $Compose config --quiet

if ($LASTEXITCODE -ne 0) {
    throw "Docker Compose validation failed."
}

Write-Host "Production Compose configuration is valid."
