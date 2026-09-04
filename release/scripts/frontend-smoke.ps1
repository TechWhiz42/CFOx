param(
    [string]$FrontendUrl = "http://localhost/"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================"
Write-Host " CFOx Frontend Smoke Test"
Write-Host "========================================"
Write-Host ""

$response = Invoke-WebRequest `
    -Uri $FrontendUrl `
    -UseBasicParsing `
    -TimeoutSec 15

if ($response.StatusCode -ne 200) {
    throw "Frontend returned HTTP $($response.StatusCode)"
}

$content = $response.Content

$checks = @(
    '<div id="root"',
    '<script',
    '/assets/'
)

$failures = @()

foreach ($check in $checks) {
    if ($content -notmatch [regex]::Escape($check)) {
        $failures += $check
    }
}

if ($failures.Count -gt 0) {
    Write-Host "[FAIL] Missing expected frontend app shell content:" -ForegroundColor Red

    foreach ($failure in $failures) {
        Write-Host " - $failure"
    }

    exit 1
}

$health = Invoke-WebRequest `
    -Uri "$($FrontendUrl.TrimEnd('/'))/health" `
    -UseBasicParsing `
    -TimeoutSec 15

if ($health.StatusCode -ne 200) {
    throw "Frontend health returned HTTP $($health.StatusCode)"
}

Write-Host "[PASS] Frontend returned expected Vite app shell." -ForegroundColor Green
Write-Host "[PASS] Frontend health endpoint returned HTTP 200." -ForegroundColor Green

exit 0