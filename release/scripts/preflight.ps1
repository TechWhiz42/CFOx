$ErrorActionPreference = "Stop"

$Root = "D:\CFOx"
$Compose = Join-Path $Root "docker-compose.production.yml"
$EnvExample = Join-Path $Root ".env.production.example"
$EnvFile = Join-Path $Root ".env.production"
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"

$Failures = @()

function Check-Path($path, $label) {
    if (Test-Path $path) {
        Write-Host "[PASS] $label"
    } else {
        Write-Host "[FAIL] $label -> $path"
        $script:Failures += $label
    }
}

function Run-Check($label, $command, [scriptblock]$action) {
    try {
        & $action
        if ($LASTEXITCODE -ne 0) {
            throw "exit code $LASTEXITCODE"
        }
        Write-Host "[PASS] $label"
    } catch {
        Write-Host "[FAIL] $label -> $($_.Exception.Message)"
        $script:Failures += $label
    }
}

Write-Host ""
Write-Host "========================================"
Write-Host " CFOx 20C Release Readiness Check"
Write-Host "========================================"
Write-Host ""

Check-Path $Root "CFOx root"
Check-Path $Compose "Production Compose file"
Check-Path $EnvExample "Production environment template"
Check-Path $Backend "Backend directory"
Check-Path $Frontend "Frontend directory"

if (Test-Path $EnvFile) {
    Write-Host "[PASS] Production environment file exists"
} else {
    Write-Host "[WARN] .env.production does not exist yet"
    Write-Host "       Create it from .env.production.example before deployment."
}

if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "[PASS] Docker CLI available"

    Run-Check "Docker daemon reachable" "docker info" {
        docker info | Out-Null
    }

    Run-Check "Production Compose syntax" "docker compose config" {
        docker compose -f $Compose config | Out-Null
    }
} else {
    Write-Host "[FAIL] Docker CLI is not available"
    $Failures += "Docker CLI available"
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "[PASS] Python available"
} else {
    Write-Host "[WARN] Python not found on PATH"
}

if (Test-Path (Join-Path $Backend "requirements.txt")) {
    Write-Host "[PASS] Backend requirements.txt"
} else {
    Write-Host "[FAIL] Backend requirements.txt"
    $Failures += "Backend requirements.txt"
}

if (Test-Path (Join-Path $Frontend "package.json")) {
    Write-Host "[PASS] Frontend package.json"
} else {
    Write-Host "[FAIL] Frontend package.json"
    $Failures += "Frontend package.json"
}

Write-Host ""
Write-Host "----------------------------------------"

if ($Failures.Count -eq 0) {
    Write-Host "READY: release prerequisites passed."
    exit 0
}

Write-Host "NOT READY: $($Failures.Count) check(s) failed."
Write-Host ""
Write-Host "Failed checks:"
$Failures | ForEach-Object { Write-Host " - $_" }
exit 1
