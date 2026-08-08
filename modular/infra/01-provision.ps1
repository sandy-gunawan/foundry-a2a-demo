[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$variables = Join-Path $PSScriptRoot "variables.ps1"
if (-not (Test-Path $variables)) {
    throw "Copy variables.example.ps1 to variables.ps1 and replace the example values first."
}
. $variables

az account set --subscription $SUBSCRIPTION_ID
$signedIn = az account show --output json | ConvertFrom-Json
if (-not $signedIn) { throw "Azure CLI is not signed in. Run az login first." }

Write-Host "Creating resource group $RESOURCE_GROUP in $LOCATION..." -ForegroundColor Cyan
az group create --name $RESOURCE_GROUP --location $LOCATION --output none

function New-FoundryAccount {
    param([string]$Region)

    Write-Host "Creating Foundry resource $ACCOUNT in $Region..." -ForegroundColor Cyan
    az cognitiveservices account create `
        --name $ACCOUNT `
        --resource-group $RESOURCE_GROUP `
        --location $Region `
        --kind AIServices `
        --sku S0 `
        --custom-domain $ACCOUNT `
        --assign-identity `
        --yes `
        --output none
}

$accountExists = az cognitiveservices account show --name $ACCOUNT --resource-group $RESOURCE_GROUP --query name --output tsv 2>$null
if (-not $accountExists) { New-FoundryAccount -Region $LOCATION }

$identityType = az cognitiveservices account show --name $ACCOUNT --resource-group $RESOURCE_GROUP --query "identity.type" --output tsv 2>$null
if (-not $identityType -or $identityType -notlike "*SystemAssigned*") {
    Write-Host "Enabling system-assigned identity on $ACCOUNT (required to create projects)..." -ForegroundColor Cyan
    az cognitiveservices account identity assign --name $ACCOUNT --resource-group $RESOURCE_GROUP --output none
}

function Find-Model {
    param([string[]]$Names)

    $models = az cognitiveservices account list-models `
        --name $ACCOUNT `
        --resource-group $RESOURCE_GROUP `
        --output json | ConvertFrom-Json

    foreach ($name in $Names) {
        $match = $models | Where-Object {
            $_.name -eq $name -and $_.format -eq "OpenAI"
        } | Sort-Object { $_.version } -Descending | Select-Object -First 1
        if ($match) { return $match }
    }
    return $null
}

$selected = Find-Model -Names @("gpt-5.4-mini", "gpt-4o-mini")
if (-not $selected) {
    throw "Neither gpt-5.4-mini nor gpt-4o-mini is available from $ACCOUNT. Set LOCATION/ACCOUNT for $FALLBACK_LOCATION and rerun."
}

$MODEL = $selected.name
$MODEL_DEPLOYMENT = $MODEL
$modelVersion = $selected.version
$globalStandard = $selected.skus | Where-Object { $_.name -eq "GlobalStandard" } | Select-Object -First 1
$skuName = if ($globalStandard) { "GlobalStandard" } else { $selected.skus[0].name }
Write-Host "Deploying $MODEL version $modelVersion with $skuName..." -ForegroundColor Cyan
az cognitiveservices account deployment create `
    --name $ACCOUNT `
    --resource-group $RESOURCE_GROUP `
    --deployment-name $MODEL_DEPLOYMENT `
    --model-name $MODEL `
    --model-version $modelVersion `
    --model-format OpenAI `
    --sku-name $skuName `
    --sku-capacity $MODEL_CAPACITY `
    --output none

$accountId = az cognitiveservices account show --name $ACCOUNT --resource-group $RESOURCE_GROUP --query id --output tsv
$accountLocation = az cognitiveservices account show --name $ACCOUNT --resource-group $RESOURCE_GROUP --query location --output tsv
$projectId = "$accountId/projects/$PROJECT"
$projectExists = az rest --method get --url "https://management.azure.com$projectId`?api-version=2025-04-01-preview" --query name --output tsv 2>$null
if (-not $projectExists) {
    Write-Host "Creating Foundry project $PROJECT..." -ForegroundColor Cyan
    $projectBody = @{ location = $accountLocation; properties = @{ displayName = $PROJECT } } | ConvertTo-Json -Depth 4 -Compress
    $bodyFile = New-TemporaryFile
    Set-Content -Path $bodyFile -Value $projectBody -Encoding utf8 -NoNewline
    az rest `
        --method put `
        --url "https://management.azure.com$projectId`?api-version=2025-04-01-preview" `
        --headers "Content-Type=application/json" `
        --body "@$bodyFile" `
        --output none
    Remove-Item $bodyFile -Force
}

# Project data plane takes a moment to become resolvable for role scope.
for ($i = 0; $i -lt 12; $i++) {
    $ready = az rest --method get --url "https://management.azure.com$projectId`?api-version=2025-04-01-preview" --query name --output tsv 2>$null
    if ($ready) { break }
    Start-Sleep -Seconds 5
}

$developerObjectId = az ad signed-in-user show --query id --output tsv
$foundryUserRoleId = "53ca6127-db72-4b80-b1b0-d745d6d5456d"
$existingRole = az role assignment list --assignee-object-id $developerObjectId --scope $projectId --query "[?roleDefinitionId=='/subscriptions/$SUBSCRIPTION_ID/providers/Microsoft.Authorization/roleDefinitions/$foundryUserRoleId'].id | [0]" --output tsv
if (-not $existingRole) {
    az role assignment create `
        --assignee-object-id $developerObjectId `
        --assignee-principal-type User `
        --role $foundryUserRoleId `
        --scope $projectId `
        --output none
}

Write-Host "Provisioning complete." -ForegroundColor Green
Write-Host "Project endpoint: https://$ACCOUNT.services.ai.azure.com/api/projects/$PROJECT"
Write-Host "Model deployment: $MODEL_DEPLOYMENT ($modelVersion, $skuName)"
Write-Host "Update MODEL and MODEL_DEPLOYMENT in variables.ps1 if fallback selected: $MODEL"