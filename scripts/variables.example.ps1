# variables.example.ps1
# ------------------------------------------------------------------
# Copy this file to "variables.ps1" and fill in YOUR real values.
# Every script in this folder does:  . .\variables.ps1   to load them.
#
#   Copy-Item .\scripts\variables.example.ps1 .\scripts\variables.ps1
#   # then edit variables.ps1
# ------------------------------------------------------------------

# --- Your Foundry resource + project ---
$ACCOUNT          = "foundryfull"                 # Foundry resource (account) name
$PROJECT          = "proj-demo-sea-001"           # Foundry project name
$SUBSCRIPTION_ID  = "00000000-0000-0000-0000-000000000000"
$RESOURCE_GROUP   = "rg-foundry"

# --- Model deployed in the project (used by the router) ---
$MODEL            = "gpt-5.4-mini"

# --- Agent names (the two specialists + the router) ---
$BILLING_AGENT    = "agt-billing"
$TECH_AGENT       = "agt-techsupport"
$ROUTER_AGENT     = "agt-router"

# --- Connection (speed-dial) names the router will use ---
$BILLING_CONN     = "conn-billing"
$TECH_CONN        = "conn-techsupport"

# --- Derived: the project data-plane endpoint (usually no need to change) ---
$PROJECT_ENDPOINT = "https://$ACCOUNT.services.ai.azure.com/api/projects/$PROJECT"

Write-Host "Loaded variables for project '$PROJECT' on account '$ACCOUNT'." -ForegroundColor Green
