param(
    [Parameter(Mandatory = $true)]
    [string]$BaseUrl
)

$ErrorActionPreference = "Stop"

function Invoke-WebhookCheck {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $url = "$($BaseUrl.TrimEnd('/'))$Path"
    Write-Host "Checking webhook endpoint: $url"

    try {
        $response = Invoke-WebRequest `
            -Uri $url `
            -Method POST `
            -ContentType "application/json" `
            -Body "{}" `
            -TimeoutSec 20

        $statusCode = [int]$response.StatusCode
    }
    catch {
        $webResponse = $_.Exception.Response
        if ($null -eq $webResponse) {
            throw "Request failed without HTTP response: $url"
        }

        $statusCode = [int]$webResponse.StatusCode
    }

    if ($statusCode -eq 404) {
        throw "Webhook endpoint not found: $url"
    }

    if ($statusCode -ge 500) {
        throw "Webhook endpoint returned server error: $url ($statusCode)"
    }

    Write-Host "OK: $url returned $statusCode"
}

Invoke-WebhookCheck -Path "/api/billing/webhooks/stripe"
Invoke-WebhookCheck -Path "/api/billing/webhooks/ccbill"
Invoke-WebhookCheck -Path "/api/billing/webhooks/usdt"
Invoke-WebhookCheck -Path "/api/billing/webhooks/telegram-stars"
Invoke-WebhookCheck -Path "/api/voice/webhook/livekit"

Write-Host "Webhook reachability checks passed."
