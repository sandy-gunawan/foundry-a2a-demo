"""Minimal A2A v0.3 code agent (Tech Support) — hand-rolled for Foundry compatibility.

Foundry's A2A tool expects an A2A **v0.3** agent card (top-level `url`,
`protocolVersion`, `preferredTransport`) and JSON-RPC `message/send`. We serve
exactly that with plain Starlette, so there is no SDK protocol-version coupling.
"""

import os
import uuid

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route


PUBLIC_URL = os.getenv("A2A_PUBLIC_URL", "http://127.0.0.1:8001").rstrip("/")


def agent_card(_request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "protocolVersion": "0.3.0",
            "name": "Code Tech Support",
            "description": "An A2A Tech Support specialist running as code in Azure Container Apps.",
            "url": PUBLIC_URL,
            "preferredTransport": "JSONRPC",
            "version": "1.0.0",
            "capabilities": {"streaming": False, "pushNotifications": False},
            "defaultInputModes": ["text/plain"],
            "defaultOutputModes": ["text/plain"],
            "skills": [
                {
                    "id": "login-help",
                    "name": "Login help",
                    "description": "Resolve password resets, account lockouts, and login errors.",
                    "tags": ["tech-support", "login"],
                    "examples": ["I cannot log in", "My password expired"],
                    "inputModes": ["text/plain"],
                    "outputModes": ["text/plain"],
                }
            ],
        }
    )


def _text_from_message(message: dict) -> str:
    parts = (message or {}).get("parts", [])
    texts = [p.get("text", "") for p in parts if isinstance(p, dict) and (p.get("kind") == "text" or "text" in p)]
    return " ".join(t for t in texts if t).strip()


async def jsonrpc(request: Request) -> JSONResponse:
    body = await request.json()
    req_id = body.get("id")
    method = body.get("method")
    if method not in ("message/send", "message/stream"):
        return JSONResponse(
            {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}
        )

    message = (body.get("params") or {}).get("message") or {}
    user_text = _text_from_message(message) or "your issue"
    reply = (
        "Code Tech Support answered through A2A: "
        f"I received '{user_text}'. Check the account status, reset the password if needed, "
        "then retry in a private browser window."
    )
    result = {
        "role": "agent",
        "parts": [{"kind": "text", "text": reply}],
        "messageId": str(uuid.uuid4()),
        "kind": "message",
    }
    return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": result})


def health(_request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


def create_app() -> Starlette:
    return Starlette(
        routes=[
            Route("/.well-known/agent-card.json", agent_card, methods=["GET"]),
            Route("/", jsonrpc, methods=["POST"]),
            Route("/health", health, methods=["GET"]),
        ]
    )


app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8001")))
