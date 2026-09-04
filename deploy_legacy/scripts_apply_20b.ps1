$ErrorActionPreference = "Stop"

$Root = "D:\CFOx"
$Backup = Join-Path $Root ".cfox_backup\20B_production_package"

# ------------------------------------------------------------
# Setup
# ------------------------------------------------------------

if (-not (Test-Path $Root)) {
    throw "CFOx root directory does not exist: $Root"
}

New-Item -ItemType Directory -Force -Path $Backup | Out-Null

# Package directory = directory containing this script
$Package = Split-Path -Parent $MyInvocation.MyCommand.Path


# ------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------

function Ensure-ParentDirectory($path) {
    $parent = Split-Path -Parent $path

    if ($parent) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
}

function Backup-IfExists($relative) {
    $source = Join-Path $Root $relative

    if (Test-Path $source) {
        $target = Join-Path $Backup $relative

        Ensure-ParentDirectory $target

        Copy-Item `
            -Path $source `
            -Destination $target `
            -Force

        Write-Host "Backed up: $relative"
    }
}

function Install-File($relative) {
    $source = Join-Path $Package $relative
    $destination = Join-Path $Root $relative

    if (-not (Test-Path $source)) {
        throw "Package file is missing: $source"
    }

    Ensure-ParentDirectory $destination

    Backup-IfExists $relative

    Copy-Item `
        -Path $source `
        -Destination $destination `
        -Force

    Write-Host "Installed: $relative"
}


# ------------------------------------------------------------
# Install Production Package
# ------------------------------------------------------------

Write-Host ""
Write-Host "========================================"
Write-Host " CFOx 20B Production Package Installer"
Write-Host "========================================"
Write-Host ""

# Backend
Install-File "backend\Dockerfile"
Install-File "backend\.dockerignore"

# Frontend
Install-File "frontend\Dockerfile"
Install-File "frontend\.dockerignore"
Install-File "frontend\nginx.conf"

# Docker Compose
Install-File "docker-compose.production.yml"

# Environment templates
Install-File ".env.example"
Install-File ".env.production.example"

# Documentation
Install-File "docs\PRODUCTION.md"

# GitHub Actions
Install-File ".github\workflows\ci.yml"


# ------------------------------------------------------------
# Backend Configuration
# ------------------------------------------------------------

# Back up backend config.
# We intentionally do NOT overwrite config.py automatically.
# Production configuration should be reviewed manually because
# existing project-specific settings must not be destroyed.

Backup-IfExists "backend\app\config.py"


# ------------------------------------------------------------
# Completion
# ------------------------------------------------------------

Write-Host ""
Write-Host "========================================"
Write-Host " CFOx 20B production package installed."
Write-Host "========================================"
Write-Host ""

Write-Host "Backups:"
Write-Host "  $Backup"
Write-Host ""

Write-Host "Next:"
Write-Host "  1. Create D:\CFOx\.env.production from .env.production.example"
Write-Host "  2. Replace all placeholder secrets."
Write-Host "  3. Keep .env.production out of git."
Write-Host "  4. Validate Docker Compose before deployment."
Write-Host ""

Write-Host "Recommended validation commands:"
Write-Host "  cd D:\CFOx"
Write-Host "  docker compose -f docker-compose.production.yml config"
Write-Host "  docker compose -f docker-compose.production.yml build"
Write-Host ""

Write-Host "Installation completed successfully."