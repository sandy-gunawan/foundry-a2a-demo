from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient

from ..config import azure_credential, settings
from ..foundry import response, run_managed_agent
from .scenario2_foundry_af import ROUTER_INSTRUCTIONS


async def handle(message: str) -> dict:
    settings.require_project()
    credential = azure_credential()
    client = FoundryChatClient(
        project_endpoint=settings.project_endpoint,
        model=settings.model,
        credential=credential,
    )
    router = Agent(client=client, name="HybridCodeRouter", instructions=ROUTER_INSTRUCTIONS)
    decision = (await router.run(message)).text.strip().upper()

    if "BILLING" in decision:
        selected_name = settings.billing_agent
        reply = await run_managed_agent(selected_name, message)
        location = "Foundry prompt agent"
    else:
        selected_name = "code-techsupport"
        specialist = Agent(
            client=client,
            name="CodeTechSupport",
            instructions=(
                "You are the in-code Tech Support department. Help with login, password, "
                "lockout, and application errors. Be concise and state that code tech support answered."
            ),
        )
        reply = (await specialist.run(message)).text
        location = "in-code Agent Framework agent"

    return response(
        selected_name,
        reply,
        [
            {"step": "router", "detail": f"Code router classified the request as {decision}."},
            {"step": "handoff", "detail": f"Request transferred to the {location}."},
        ],
    )