param(
    [Parameter(Mandatory = $true)]
    [string]$BaseUrl
)

$ErrorActionPreference = "Stop"

function Invoke-HealthCheck {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $url = "$($BaseUrl.TrimEnd('/'))$Path"
    Write-Host "Checking $url"
    $response = Invoke-WebRequest -Uri $url -Method GET -TimeoutSec 20
    if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 300) {
        throw "Health check failed: $url returned status $($response.StatusCode)"
    }
}

Invoke-HealthCheck -Path "/health"
Invoke-HealthCheck -Path "/api/inference/system/health"
Invoke-HealthCheck -Path "/api/images/callbacks/health"

Write-Host "Smoke checks passed."
