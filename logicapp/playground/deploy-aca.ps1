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
    [string]$ImageTag      = "logicapp-playground:v2",
    [string]$TargetPort    = "8501"
)

$ErrorActionPreference = "Stop"

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
        --min-replicas 1 --max-replicas 2 `
        --only-show-errors | Out-Null
}
else {
    Write-Host "==> Updating existing Container App '$AppName'..." -ForegroundColor Cyan
    az containerapp update --name $AppName --resource-group $ResourceGroup `
        --image $fullImage `
        --remove-env-vars LOGIC_APP_URL `
        --only-show-errors | Out-Null
}

$fqdn = az containerapp show --name $AppName --resource-group $ResourceGroup --query "properties.configuration.ingress.fqdn" -o tsv
Write-Host ""
Write-Host "Deployed. Open the playground at:" -ForegroundColor Green
Write-Host "  https://$fqdn" -ForegroundColor Green
Write-Host ""
Write-Host "Set the Logic App URL from the app's Settings sidebar (top-left >) - no env, no redeploy." -ForegroundColor DarkGray
