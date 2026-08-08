from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient

from ..config import azure_credential, settings
from ..foundry import response, run_managed_agent


ROUTER_INSTRUCTIONS = """You are a switchboard operator. Classify the request.
Return exactly BILLING for invoices, payments, refunds, or charges.
Return exactly TECH for logins, passwords, lockouts, or error messages.
If uncertain, choose the closest department. Do not add punctuation or explanation."""


async def handle(message: str) -> dict:
    settings.require_project()
    router = Agent(
        client=FoundryChatClient(
            project_endpoint=settings.project_endpoint,
            model=settings.model,
            credential=azure_credential(),
        ),
        name="CodeRouter",
        instructions=ROUTER_INSTRUCTIONS,
    )
    decision = (await router.run(message)).text.strip().upper()
    selected_name = settings.billing_agent if "BILLING" in decision else settings.tech_agent

    reply = await run_managed_agent(selected_name, message)
    return response(
        selected_name,
        reply,
        [
            {"step": "router", "detail": f"Agent Framework classified the request as {decision}."},
            {"step": "handoff", "detail": f"Code invoked Foundry agent {selected_name}."},
        ],
    )