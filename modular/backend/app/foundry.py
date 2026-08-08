import asyncio
from typing import Any

from azure.ai.projects import AIProjectClient

from .config import azure_credential, settings


async def run_managed_agent(agent_name: str, message: str) -> str:
    settings.require_project()

    def invoke() -> str:
        project = AIProjectClient(
            endpoint=settings.project_endpoint,
            credential=azure_credential(),
        )
        response = project.get_openai_client().responses.create(
            input=message,
            extra_body={
                "agent_reference": {
                    "name": agent_name,
                    "type": "agent_reference",
                }
            },
        )
        return response.output_text

    return await asyncio.to_thread(invoke)


def response(agent: str, reply: str, trace: list[dict[str, Any]]) -> dict[str, Any]:
    return {"agent": agent, "reply": reply, "trace": trace}