import argparse
import json
import os
from pathlib import Path

import requests
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import A2APreviewTool, PromptAgentDefinition
from azure.identity import AzureCliCredential


BILLING_INSTRUCTIONS = """You are the Billing department. Handle invoices, payments,
refunds, and duplicate or incorrect charges. Give a short demo response and clearly say
that Billing answered. Do not claim to have accessed a real customer account."""

TECH_INSTRUCTIONS = """You are Tech Support. Handle logins, password resets, account
lockouts, and error messages. Give a short demo response and clearly say that Tech Support
answered. Do not claim to have changed a real customer account."""

ROUTER_INSTRUCTIONS = """You are a company switchboard operator. Never answer the issue
yourself. Transfer each request to exactly one A2A specialist: Billing for invoices,
payments, refunds, or charges; Tech Support for logins, passwords, lockouts, or errors.
Return the selected specialist's response."""


def env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


def create_connection(
    token: str,
    connection_id: str,
    target: str,
    auth_type: str,
    metadata: dict | None = None,
) -> None:
    body = {
        "properties": {
            "authType": auth_type,
            "group": "ServicesAndApps",
            "category": "RemoteA2A",
            "target": target,
            "isSharedToAll": True,
            "sharedUserList": [],
            "credentials": {},
            "metadata": {"ApiType": "Azure", **(metadata or {})},
        }
    }
    if auth_type == "AgenticIdentityToken":
        body["properties"]["audience"] = "https://ai.azure.com"
    response = requests.put(
        f"https://management.azure.com{connection_id}?api-version=2025-04-01-preview",
        headers={"Authorization": f"Bearer {token}"},
        json=body,
        timeout=60,
    )
    response.raise_for_status()


def enable_a2a(
    endpoint: str,
    token: str,
    name: str,
    description: str,
    skill_id: str,
    skill_name: str,
    examples: list[str],
) -> None:
    body = {
        "agent_card": {
            "description": description,
            "version": "1.0",
            "skills": [
                {
                    "id": skill_id,
                    "name": skill_name,
                    "description": description,
                    "examples": examples,
                }
            ],
        },
        "agent_endpoint": {"protocol_configuration": {"responses": {}, "a2a": {}}},
    }
    response = requests.patch(
        f"{endpoint}/agents/{name}?api-version=v1",
        headers={"Authorization": f"Bearer {token}"},
        json=body,
        timeout=60,
    )
    response.raise_for_status()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--code-agent-url", help="Public base URL of the Scenario 3b A2A server")
    args = parser.parse_args()

    endpoint = env("PROJECT_ENDPOINT").rstrip("/")
    model = env("MODEL")
    subscription_id = env("SUBSCRIPTION_ID")
    resource_group = env("RESOURCE_GROUP")
    account = env("ACCOUNT")
    project_name = env("PROJECT")
    billing_agent = os.getenv("BILLING_AGENT", "agt-billing")
    tech_agent = os.getenv("TECH_AGENT", "agt-techsupport")
    router_agent = os.getenv("ROUTER_AGENT", "agt-router")
    hybrid_router = os.getenv("HYBRID_ROUTER_AGENT", "agt-hybrid-router")
    billing_conn_name = os.getenv("BILLING_CONN", "conn-billing")
    tech_conn_name = os.getenv("TECH_CONN", "conn-techsupport")
    code_conn_name = os.getenv("CODE_TECH_CONN", "conn-code-techsupport")

    credential = AzureCliCredential()
    project = AIProjectClient(endpoint=endpoint, credential=credential)
    billing = project.agents.create_version(
        agent_name=billing_agent,
        definition=PromptAgentDefinition(model=model, instructions=BILLING_INSTRUCTIONS),
    )
    tech = project.agents.create_version(
        agent_name=tech_agent,
        definition=PromptAgentDefinition(model=model, instructions=TECH_INSTRUCTIONS),
    )

    data_token = credential.get_token("https://ai.azure.com/.default").token
    enable_a2a(
        endpoint,
        data_token,
        billing_agent,
        "Billing department for invoices, payments, refunds, and charges.",
        "billing-help",
        "Billing help",
        ["I was charged twice", "Where is my refund?"],
    )
    enable_a2a(
        endpoint,
        data_token,
        tech_agent,
        "Tech Support for logins, password resets, lockouts, and errors.",
        "login-help",
        "Login help",
        ["I cannot log in", "My password expired"],
    )

    base_connection_id = (
        f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}"
        f"/providers/Microsoft.CognitiveServices/accounts/{account}/projects/{project_name}/connections"
    )
    management_token = credential.get_token("https://management.azure.com/.default").token
    create_connection(
        management_token,
        f"{base_connection_id}/{billing_conn_name}",
        f"{endpoint}/agents/{billing_agent}/endpoint/protocols/a2a",
        "AgenticIdentityToken",
    )
    create_connection(
        management_token,
        f"{base_connection_id}/{tech_conn_name}",
        f"{endpoint}/agents/{tech_agent}/endpoint/protocols/a2a",
        "AgenticIdentityToken",
    )

    billing_conn = project.connections.get(billing_conn_name)
    tech_conn = project.connections.get(tech_conn_name)
    router = project.agents.create_version(
        agent_name=router_agent,
        definition=PromptAgentDefinition(
            model=model,
            instructions=ROUTER_INSTRUCTIONS,
            tools=[
                A2APreviewTool(project_connection_id=billing_conn.id),
                A2APreviewTool(project_connection_id=tech_conn.id),
            ],
        ),
    )

    result = {
        "billing": {"name": billing.name, "version": billing.version},
        "tech": {"name": tech.name, "version": tech.version},
        "router": {"name": router.name, "version": router.version},
    }

    if args.code_agent_url:
        create_connection(
            management_token,
            f"{base_connection_id}/{code_conn_name}",
            args.code_agent_url.rstrip("/"),
            "None",
            {"agentCardPath": "/.well-known/agent-card.json"},
        )
        code_conn = project.connections.get(code_conn_name)
        hybrid = project.agents.create_version(
            agent_name=hybrid_router,
            definition=PromptAgentDefinition(
                model=model,
                instructions=ROUTER_INSTRUCTIONS,
                tools=[
                    A2APreviewTool(project_connection_id=billing_conn.id),
                    A2APreviewTool(project_connection_id=code_conn.id),
                ],
            ),
        )
        result["hybrid_router"] = {"name": hybrid.name, "version": hybrid.version}

    output = Path(__file__).with_name("agent-versions.json")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()