# 2-create-connections.ps1
# ------------------------------------------------------------------
# PART B / Step B1 — Create one A2A CONNECTION per specialist.
#
# WHAT THIS DOES (switchboard analogy):
#   Saves a SPEED-DIAL on the operator's phone for each department's
#   extension, including HOW to prove identity (Entra agentic-identity).
#
# WHY THESE SETTINGS (verified from Microsoft docs):
#   - category  = "RemoteA2A"            -> this connection is an A2A target
#   - authType  = "AgenticIdentityToken" -> use Entra badge, NOT an API key
#   - audience  = "https://ai.azure.com" -> who the badge is for
#   - target    = the specialist's A2A endpoint URL
#   For a Foundry target, do NOT set an agent-card path; Foundry resolves it.
#
# PREREQS:
#   - az login
#   - Step A3 already run (specialists have A2A enabled).
#   - variables.ps1 filled in.
# ------------------------------------------------------------------

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\variables.ps1"

# Management-plane token (audience: Azure Resource Manager)
$TOKEN = az account get-access-token --scope https://management.azure.com/.default --query accessToken -o tsv
if (-not $TOKEN) { throw "Could not get a management token. Run 'az login' first." }
$headers = @{ Authorization = "Bearer $TOKEN"; "Content-Type" = "application/json" }

function New-A2AConnection {
    param(
        [string]$ConnectionName,
        [string]$TargetAgent
    )

    $targetUrl = "$PROJECT_ENDPOINT/agents/$TargetAgent/endpoint/protocols/a2a"
    Write-Host "`nCreating speed-dial '$ConnectionName' -> $TargetAgent ..." -ForegroundColor Cyan

    $body = @{
        properties = @{
            authType    = "AgenticIdentityToken"   # Entra badge, not a key
            category    = "RemoteA2A"
            target      = $targetUrl
            audience    = "https://ai.azure.com"
            Credentials = @{}
            metadata    = @{}
        }
    } | ConvertTo-Json -Depth 5

    $uri = "https://management.azure.com/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/$ACCOUNT/projects/$PROJECT/connections/$ConnectionName`?api-version=2025-04-01-preview"
    Invoke-RestMethod -Method Put -Uri $uri -Headers $headers -Body $body | Out-Null
    Write-Host "  OK. Connection '$ConnectionName' created." -ForegroundColor Green
}

New-A2AConnection -ConnectionName $BILLING_CONN -TargetAgent $BILLING_AGENT
New-A2AConnection -ConnectionName $TECH_CONN    -TargetAgent $TECH_AGENT

Write-Host "`nDone. The router now has two speed-dials: '$BILLING_CONN' and '$TECH_CONN'." -ForegroundColor Green
Write-Host "Next: run 3-create-router.py to build the router with the A2A tool." -ForegroundColor DarkGray
