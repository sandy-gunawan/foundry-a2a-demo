[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$variables = Join-Path $PSScriptRoot "variables.ps1"
if (-not (Test-Path $variables)) { throw "Create infra/variables.ps1 first." }
. $variables

$root = Split-Path $PSScriptRoot -Parent
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Create modular/.venv and install backend/requirements.txt first." }

az account set --subscription $SUBSCRIPTION_ID
az extension add --name containerapp --upgrade --yes --output none

$registryExists = az acr show --name $CONTAINER_REGISTRY --resource-group $RESOURCE_GROUP --query name --output tsv 2>$null
if (-not $registryExists) {
    az acr create --name $CONTAINER_REGISTRY --resource-group $RESOURCE_GROUP --sku Basic --admin-enabled true --output none
}

Push-Location $root
try {
    az acr build --registry $CONTAINER_REGISTRY --image "a2a-backend:latest" --file backend/Dockerfile . --output none
    az acr build --registry $CONTAINER_REGISTRY --image "a2a-codeagent:latest" --file codeagent/Dockerfile . --output none
}
finally {
    Pop-Location
}

$environmentExists = az containerapp env show --name $ACA_ENVIRONMENT --resource-group $RESOURCE_GROUP --query name --output tsv 2>$null
if (-not $environmentExists) {
    az containerapp env create --name $ACA_ENVIRONMENT --resource-group $RESOURCE_GROUP --location $LOCATION --output none
}

$registryServer = az acr show --name $CONTAINER_REGISTRY --query loginServer --output tsv
$registryUser = az acr credential show --name $CONTAINER_REGISTRY --query username --output tsv
$registryPassword = az acr credential show --name $CONTAINER_REGISTRY --query passwords[0].value --output tsv

$codeExists = az containerapp show --name $CODE_AGENT_APP --resource-group $RESOURCE_GROUP --query name --output tsv 2>$null
if (-not $codeExists) {
    az containerapp create `
        --name $CODE_AGENT_APP `
        --resource-group $RESOURCE_GROUP `
        --environment $ACA_ENVIRONMENT `
        --image "$registryServer/a2a-codeagent:latest" `
        --registry-server $registryServer `
        --registry-username $registryUser `
        --registry-password $registryPassword `
        --target-port 8001 `
        --ingress external `
        --min-replicas 1 `
        --max-replicas 3 `
        --output none
}
else {
    az containerapp update --name $CODE_AGENT_APP --resource-group $RESOURCE_GROUP --image "$registryServer/a2a-codeagent:latest" --output none
}

$codeFqdn = az containerapp show --name $CODE_AGENT_APP --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn --output tsv
$codeUrl = "https://$codeFqdn"
az containerapp update `
    --name $CODE_AGENT_APP `
    --resource-group $RESOURCE_GROUP `
    --set-env-vars "A2A_PUBLIC_URL=$codeUrl" `
    --output none

$env:PROJECT_ENDPOINT = $PROJECT_ENDPOINT
$env:MODEL = $MODEL_DEPLOYMENT
$env:SUBSCRIPTION_ID = $SUBSCRIPTION_ID
$env:RESOURCE_GROUP = $RESOURCE_GROUP
$env:ACCOUNT = $ACCOUNT
$env:PROJECT = $PROJECT
$env:BILLING_AGENT = $BILLING_AGENT
$env:TECH_AGENT = $TECH_AGENT
$env:ROUTER_AGENT = $ROUTER_AGENT
$env:HYBRID_ROUTER_AGENT = $HYBRID_ROUTER_AGENT
$env:BILLING_CONN = $BILLING_CONN
$env:TECH_CONN = $TECH_CONN
$env:CODE_TECH_CONN = $CODE_TECH_CONN
& $python (Join-Path $PSScriptRoot "02-create-foundry-agents.py") --code-agent-url $codeUrl

$versions = Get-Content (Join-Path $PSScriptRoot "agent-versions.json") | ConvertFrom-Json
$backendExists = az containerapp show --name $BACKEND_APP --resource-group $RESOURCE_GROUP --query name --output tsv 2>$null
if (-not $backendExists) {
    az containerapp create `
        --name $BACKEND_APP `
        --resource-group $RESOURCE_GROUP `
        --environment $ACA_ENVIRONMENT `
        --image "$registryServer/a2a-backend:latest" `
        --registry-server $registryServer `
        --registry-username $registryUser `
        --registry-password $registryPassword `
        --target-port 8000 `
        --ingress external `
        --system-assigned `
        --min-replicas 1 `
        --max-replicas 3 `
        --env-vars `
            "PROJECT_ENDPOINT=$PROJECT_ENDPOINT" `
            "MODEL=$MODEL_DEPLOYMENT" `
            "BILLING_AGENT=$BILLING_AGENT" `
            "BILLING_AGENT_VERSION=$($versions.billing.version)" `
            "TECH_AGENT=$TECH_AGENT" `
            "TECH_AGENT_VERSION=$($versions.tech.version)" `
            "ROUTER_AGENT=$ROUTER_AGENT" `
            "HYBRID_ROUTER_AGENT=$HYBRID_ROUTER_AGENT" `
        --output none
}
else {
    az containerapp update `
        --name $BACKEND_APP `
        --resource-group $RESOURCE_GROUP `
        --image "$registryServer/a2a-backend:latest" `
        --set-env-vars `
            "PROJECT_ENDPOINT=$PROJECT_ENDPOINT" `
            "MODEL=$MODEL_DEPLOYMENT" `
            "BILLING_AGENT=$BILLING_AGENT" `
            "BILLING_AGENT_VERSION=$($versions.billing.version)" `
            "TECH_AGENT=$TECH_AGENT" `
            "TECH_AGENT_VERSION=$($versions.tech.version)" `
            "ROUTER_AGENT=$ROUTER_AGENT" `
            "HYBRID_ROUTER_AGENT=$HYBRID_ROUTER_AGENT" `
        --output none
}

$principalId = az containerapp identity show --name $BACKEND_APP --resource-group $RESOURCE_GROUP --query principalId --output tsv
$accountId = az cognitiveservices account show --name $ACCOUNT --resource-group $RESOURCE_GROUP --query id --output tsv
$projectId = "$accountId/projects/$PROJECT"
$foundryAgentConsumerRoleId = "eed3b665-ab3a-47b6-8f48-c9382fb1dad6"
$assignment = az role assignment list --assignee-object-id $principalId --scope $projectId --query "[?roleDefinitionId=='/subscriptions/$SUBSCRIPTION_ID/providers/Microsoft.Authorization/roleDefinitions/$foundryAgentConsumerRoleId'].id | [0]" --output tsv
if (-not $assignment) {
    az role assignment create `
        --assignee-object-id $principalId `
        --assignee-principal-type ServicePrincipal `
        --role $foundryAgentConsumerRoleId `
        --scope $projectId `
        --output none
}

$backendFqdn = az containerapp show --name $BACKEND_APP --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn --output tsv
Write-Host "Deployment complete: https://$backendFqdn" -ForegroundColor Green
Write-Host "Code-agent card: $codeUrl/.well-known/agent-card.json"