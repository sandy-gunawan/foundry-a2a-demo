# 1-enable-a2a.ps1
# ------------------------------------------------------------------
# PART A / Step A3 — Turn ON incoming A2A for both specialist agents.
#
# WHAT THIS DOES (switchboard analogy):
#   Publishes each department's phone EXTENSION in the company directory,
#   and writes its NAMEPLATE (agent card) so the operator can find it.
#
# WHY A SCRIPT:
#   Enabling the A2A protocol on an agent is NOT clickable in the Foundry
#   portal yet, so we call the REST API. (Verified from Microsoft docs.)
#
# PREREQS:
#   - az login   (get your badge / Entra token)
#   - Both agents already created (Step A1) as PROMPT agents.
#   - variables.ps1 filled in.
# ------------------------------------------------------------------

$ErrorActionPreference = "Stop"

# Load your values
. "$PSScriptRoot\variables.ps1"

# Get an Entra token for the Foundry data-plane (audience: https://ai.azure.com)
$TOKEN = az account get-access-token --resource https://ai.azure.com --query accessToken -o tsv
if (-not $TOKEN) { throw "Could not get a token. Run 'az login' first." }
$headers = @{ Authorization = "Bearer $TOKEN"; "Content-Type" = "application/json" }

function Enable-A2A {
    param(
        [string]$AgentName,
        [string]$Description,
        [string]$SkillId,
        [string]$SkillName,
        [string]$SkillDescription,
        [string[]]$Examples
    )

    Write-Host "`nEnabling A2A for '$AgentName'..." -ForegroundColor Cyan

    # Body = agent card (nameplate) + turn on both 'responses' and 'a2a' protocols
    $body = @{
        agent_card = @{
            description = $Description
            version     = "1.0"
            skills      = @(
                @{
                    id          = $SkillId
                    name        = $SkillName
                    description  = $SkillDescription
                    examples    = $Examples
                }
            )
        }
        agent_endpoint = @{
            protocol_configuration = @{
                responses = @{}   # required base protocol
                a2a       = @{}   # <-- this turns ON incoming A2A
            }
        }
    } | ConvertTo-Json -Depth 6

    $uri = "$PROJECT_ENDPOINT/agents/$AgentName`?api-version=v1"
    Invoke-RestMethod -Method Patch -Uri $uri -Headers $headers -Body $body | Out-Null

    # Verify: fetch the v1.0 agent card back
    $cardUri = "$PROJECT_ENDPOINT/agents/$AgentName/endpoint/protocols/a2a/agentCard/v1.0"
    $card = Invoke-RestMethod -Method Get -Uri $cardUri -Headers @{ Authorization = "Bearer $TOKEN" }
    Write-Host "  OK. Card description: '$($card.description)'" -ForegroundColor Green
    Write-Host "  A2A endpoint: $PROJECT_ENDPOINT/agents/$AgentName/endpoint/protocols/a2a" -ForegroundColor DarkGray
}

# --- Billing department ---
Enable-A2A `
    -AgentName        $BILLING_AGENT `
    -Description      "Billing department. Handles invoices, payments, refunds, and duplicate or incorrect charges." `
    -SkillId          "refund-lookup" `
    -SkillName        "Refund lookup" `
    -SkillDescription "Find and explain charges, duplicates, and refunds." `
    -Examples         @("I was charged twice", "Where is my refund?")

# --- Tech Support department ---
Enable-A2A `
    -AgentName        $TECH_AGENT `
    -Description      "Tech Support. Handles logins, password resets, account lockouts, and error messages." `
    -SkillId          "login-help" `
    -SkillName        "Login help" `
    -SkillDescription "Resolve password resets and login errors." `
    -Examples         @("I can't log in", "Password expired")

Write-Host "`nDone. Both specialists are now A2A servers (extensions published)." -ForegroundColor Green
