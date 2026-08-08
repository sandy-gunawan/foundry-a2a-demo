"""Wire Scenario 3b: connect the deployed code agent and build the hybrid router.

Reuses the existing conn-billing connection; creates conn-code-techsupport pointing
at the public code-agent URL, then a hybrid router with both A2A tools.

Usage: python infra/03b-wire-hybrid.py https://<code-agent-fqdn>
"""

import os
import sys

import requests
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import A2APreviewTool, PromptAgentDefinition
from azure.identity import AzureCliCredential


def _env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(
            f"Missing environment variable: {name}. Export your infra/variables.ps1 values first, e.g.\n"
            "  . .\\infra\\variables.ps1\n"
            "  $env:SUBSCRIPTION_ID=$SUBSCRIPTION_ID; $env:RESOURCE_GROUP=$RESOURCE_GROUP\n"
            "  $env:ACCOUNT=$ACCOUNT; $env:PROJECT=$PROJECT; $env:MODEL=$MODEL_DEPLOYMENT"
        )
    return value


SUB = _env("SUBSCRIPTION_ID")
RG = _env("RESOURCE_GROUP")
ACCOUNT = _env("ACCOUNT")
PROJECT = _env("PROJECT")
ENDPOINT = f"https://{ACCOUNT}.services.ai.azure.com/api/projects/{PROJECT}"
MODEL = os.getenv("MODEL", "gpt-5.4-mini")
BILLING_CONN = os.getenv("BILLING_CONN", "conn-billing")
CODE_CONN = os.getenv("CODE_TECH_CONN", "conn-code-techsupport")
HYBRID_ROUTER = os.getenv("HYBRID_ROUTER_AGENT", "agt-hybrid-router")

ROUTER_INSTRUCTIONS = """You are a company switchboard operator. Never answer the issue
yourself. Transfer each request to exactly one connected specialist: Billing for invoices,
payments, refunds, or charges; Tech Support for logins, passwords, lockouts, or errors.
Return the selected specialist's response."""


def create_code_connection(mgmt_token: str, code_url: str) -> None:
    base = (
        f"/subscriptions/{SUB}/resourceGroups/{RG}/providers/Microsoft.CognitiveServices"
        f"/accounts/{ACCOUNT}/projects/{PROJECT}/connections"
    )
    # The code agent is public/anonymous; try no-auth types in order until one is accepted.
    for auth_type in ("None", "Anonymous", "CustomKeys"):
        body = {
            "properties": {
                "authType": auth_type,
                "group": "ServicesAndApps",
                "category": "RemoteA2A",
                "target": code_url,
                "isSharedToAll": True,
                "sharedUserList": [],
                "credentials": {} if auth_type != "CustomKeys" else {"keys": {"x-demo": "public"}},
                "metadata": {"ApiType": "Azure"},
            }
        }
        resp = requests.put(
            f"https://management.azure.com{base}/{CODE_CONN}?api-version=2025-04-01-preview",
            headers={"Authorization": f"Bearer {mgmt_token}"},
            json=body,
            timeout=60,
        )
        print(f"  authType={auth_type} -> {resp.status_code}")
        if resp.status_code < 300:
            print(f"  connection created with authType={auth_type}")
            return
        print(f"  rejected: {resp.text[:300]}")
    raise SystemExit("Could not create the code-agent connection with any no-auth type.")


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Pass the code-agent base URL, e.g. https://ca-a2a-codeagent.<region>.azurecontainerapps.io")
    code_url = sys.argv[1].rstrip("/")

    cred = AzureCliCredential()
    project = AIProjectClient(endpoint=ENDPOINT, credential=cred)
    mgmt = cred.get_token("https://management.azure.com/.default").token

    print("Creating code-agent connection...")
    create_code_connection(mgmt, code_url)

    billing_conn = project.connections.get(BILLING_CONN)
    code_conn = project.connections.get(CODE_CONN)
    print("Building hybrid router...")
    router = project.agents.create_version(
        agent_name=HYBRID_ROUTER,
        definition=PromptAgentDefinition(
            model=MODEL,
            instructions=ROUTER_INSTRUCTIONS,
            tools=[
                A2APreviewTool(project_connection_id=billing_conn.id),
                A2APreviewTool(project_connection_id=code_conn.id),
            ],
        ),
    )
    print(f"Hybrid router ready: {router.name} v{router.version}")


if __name__ == "__main__":
    main()
