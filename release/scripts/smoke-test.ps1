param(
    [string]$BackendUrl = "http://127.0.0.1:8000",
    [string]$FrontendUrl = "http://localhost/"
)

$ErrorActionPreference = "Stop"

$Failures = @()

function Test-Url {
    param(
        [string]$Name,
        [string]$Url,
        [int]$ExpectedStatus = 200
    )

    try {
        $response = Invoke-WebRequest `
            -Uri $Url `
            -UseBasicParsing `
            -TimeoutSec 15

        if ([int]$response.StatusCode -eq $ExpectedStatus) {
            Write-Host "[PASS] $Name -> HTTP $($response.StatusCode)" -ForegroundColor Green
        } else {
            Write-Host "[FAIL] $Name -> expected HTTP $ExpectedStatus, got HTTP $($response.StatusCode)" -ForegroundColor Red
            $script:Failures += $Name
        }
    } catch {
        Write-Host "[FAIL] $Name -> $($_.Exception.Message)" -ForegroundColor Red
        $script:Failures += $Name
    }
}

Write-Host ""
Write-Host "========================================"
Write-Host " CFOx Smoke Test"
Write-Host "========================================"
Write-Host ""

Test-Url "Backend liveness" "$BackendUrl/healthz"
Test-Url "Backend readiness" "$BackendUrl/readyz"
Test-Url "Frontend" $FrontendUrl

Write-Host ""

if ($Failures.Count -eq 0) {
    Write-Host "SMOKE TEST PASSED" -ForegroundColor Green
    exit 0
}

Write-Host "SMOKE TEST FAILED: $($Failures.Count) failure(s)" -ForegroundColor Red
$Failures | ForEach-Object {
    Write-Host " - $_"
}

exit 1