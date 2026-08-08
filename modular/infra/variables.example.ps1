$SUBSCRIPTION_ID = "00000000-0000-0000-0000-000000000000"
$RESOURCE_GROUP = "rg_a2a_foundry"
$LOCATION = "southeastasia"
$FALLBACK_LOCATION = "eastus2"

# Cognitive Services account names must be globally unique and use letters/numbers/hyphens.
$ACCOUNT = "a2afoundry-yourinitials-001"
$PROJECT = "proj-a2a-modular"
$MODEL = "gpt-5.4-mini"
$MODEL_DEPLOYMENT = "gpt-5.4-mini"
$MODEL_CAPACITY = 10

$BILLING_AGENT = "agt-billing"
$TECH_AGENT = "agt-techsupport"
$ROUTER_AGENT = "agt-router"
$HYBRID_ROUTER_AGENT = "agt-hybrid-router"
$BILLING_CONN = "conn-billing"
$TECH_CONN = "conn-techsupport"
$CODE_TECH_CONN = "conn-code-techsupport"

$ACA_ENVIRONMENT = "acae-a2a-foundry"
$BACKEND_APP = "ca-a2a-switchboard"
$CODE_AGENT_APP = "ca-a2a-codeagent"
$CONTAINER_REGISTRY = "acra2ayourinitials001"

$PROJECT_ENDPOINT = "https://$ACCOUNT.services.ai.azure.com/api/projects/$PROJECT"