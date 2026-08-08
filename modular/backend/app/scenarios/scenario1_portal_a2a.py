from ..config import settings
from ..foundry import response, run_managed_agent


async def handle(message: str) -> dict:
    reply = await run_managed_agent(settings.router_agent, message)
    return response(
        settings.router_agent,
        reply,
        [
            {"step": "user", "detail": "Message sent to the Foundry router."},
            {"step": "a2a", "detail": "Router selected one Foundry specialist."},
            {"step": "reply", "detail": "Specialist response returned through the router."},
        ],
    )