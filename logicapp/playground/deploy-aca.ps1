# Deploy the Streamlit playground (playground.py) to Azure Container Apps.
#
# The Logic App URL is CONFIGURABLE and stored as an ACA *secret* (never baked into the image).
# Set it in your terminal first (the URL contains a secret sig=...), then run this script:
#
#   $env:LOGIC_APP_URL = "<your trigger URL>"
#   pwsh -File .\deploy-aca.ps1
#
# All resource names are parameters with sensible defaults for rg_a2a_foundry.

param(
    [string]$ResourceGroup = "rg_a2a_foundry",
    [string]$Location      = "southeastasia",
    [string]$Registry      = "acra2asg0808x7q2",       # existing ACR (name only)
    [string]$Environment   = "acae-a2a-foundry",       # existing Container Apps environment
    [string]$AppName       = "ca-logicapp-playground",
    [string]$ImageTag      = "logicapp-playground:v1",
    [string]$TargetPort    = "8501",
    [string]$LogicAppUrl   = $env:LOGIC_APP_URL
)

$ErrorActionPreference = "Stop"

if (-not $LogicAppUrl) {
    $LogicAppUrl = "SET_IN_PORTAL"
    Write-Host "LOGIC_APP_URL not set - deploying with a placeholder." -ForegroundColor Yellow
    Write-Host "After deploy, set the real URL in the portal: Container App -> Settings -> Secrets -> 'logic-app-url' -> then restart the revision." -ForegroundColor Yellow
}

Write-Host "==> Ensuring resource group '$ResourceGroup' exists..." -ForegroundColor Cyan
az group create --name $ResourceGroup --location $Location --only-show-errors | Out-Null

Write-Host "==> Building image '$ImageTag' in ACR '$Registry' (from this folder)..." -ForegroundColor Cyan
az acr build --registry $Registry --image $ImageTag . --only-show-errors

$acrLoginServer = az acr show --name $Registry --query loginServer -o tsv
$fullImage = "$acrLoginServer/$ImageTag"

# Reliable ACR pull for the container app: use admin credentials.
Write-Host "==> Fetching ACR credentials for image pull..." -ForegroundColor Cyan
az acr update --name $Registry --admin-enabled true --only-show-errors | Out-Null
$acrUser = az acr credential show --name $Registry --query username -o tsv
$acrPass = az acr credential show --name $Registry --query "passwords[0].value" -o tsv

$exists = az containerapp show --name $AppName --resource-group $ResourceGroup --query name -o tsv 2>$null

if (-not $exists) {
    Write-Host "==> Creating Container App '$AppName'..." -ForegroundColor Cyan
    az containerapp create `
        --name $AppName `
        --resource-group $ResourceGroup `
        --environment $Environment `
        --image $fullImage `
        --target-port $TargetPort `
        --ingress external `
        --registry-server $acrLoginServer `
        --registry-username $acrUser `
        --registry-password $acrPass `
        --secrets "logic-app-url=$LogicAppUrl" `
        --env-vars "LOGIC_APP_URL=secretref:logic-app-url" `
        --min-replicas 1 --max-replicas 2 `
        --only-show-errors | Out-Null
}
else {
    Write-Host "==> Updating existing Container App '$AppName'..." -ForegroundColor Cyan
    az containerapp secret set --name $AppName --resource-group $ResourceGroup `
        --secrets "logic-app-url=$LogicAppUrl" --only-show-errors | Out-Null
    az containerapp update --name $AppName --resource-group $ResourceGroup `
        --image $fullImage `
        --set-env-vars "LOGIC_APP_URL=secretref:logic-app-url" `
        --only-show-errors | Out-Null
}

$fqdn = az containerapp show --name $AppName --resource-group $ResourceGroup --query "properties.configuration.ingress.fqdn" -o tsv
Write-Host ""
Write-Host "Deployed. Open the playground at:" -ForegroundColor Green
Write-Host "  https://$fqdn" -ForegroundColor Green
Write-Host ""
Write-Host "To change the Logic App URL later (no rebuild):" -ForegroundColor DarkGray
Write-Host "  az containerapp secret set -n $AppName -g $ResourceGroup --secrets logic-app-url='<new-url>'" -ForegroundColor DarkGray
Write-Host "  az containerapp revision restart -n $AppName -g $ResourceGroup" -ForegroundColor DarkGray
