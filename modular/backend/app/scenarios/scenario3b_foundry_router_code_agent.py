from ..config import settings
from ..foundry import response, run_managed_agent


async def handle(message: str) -> dict:
    reply = await run_managed_agent(settings.hybrid_router_agent, message)
    return response(
        settings.hybrid_router_agent,
        reply,
        [
            {"step": "user", "detail": "Message sent to the Foundry hybrid router."},
            {"step": "a2a", "detail": "Router selected a Foundry or Container Apps specialist."},
            {"step": "reply", "detail": "A2A response returned through the Foundry router."},
        ],
    )