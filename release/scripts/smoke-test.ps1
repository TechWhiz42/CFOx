param(
    [string]$BackendUrl = "http://127.0.0.1:8000",
    [string]$FrontendUrl = "http://127.0.0.1"
)

$ErrorActionPreference = "Stop"

function Check-Url {
    param(
        [string]$Url,
        [string]$Label
    )

    try {
        $response = Invoke-WebRequest `
            -Uri $Url `
            -UseBasicParsing `
            -TimeoutSec 10

        Write-Host "[PASS] $Label -> HTTP $($response.StatusCode)"
        return $true
    }
    catch {
        Write-Host "[FAIL] $Label -> $($_.Exception.Message)"
        return $false
    }
}

Write-Host ""
Write-Host "========================================"
Write-Host " CFOx Production Smoke Test"
Write-Host "========================================"
Write-Host ""

$backendDocs = Check-Url `
    -Url "$BackendUrl/docs" `
    -Label "Backend OpenAPI endpoint"

$frontend = Check-Url `
    -Url $FrontendUrl `
    -Label "Frontend"

Write-Host ""

if ($backendDocs -and $frontend) {
    Write-Host "========================================"
    Write-Host " SMOKE TEST PASSED"
    Write-Host "========================================"
    Write-Host ""

    exit 0
}

Write-Host "========================================"
Write-Host " SMOKE TEST FAILED"
Write-Host "========================================"
Write-Host ""

exit 1