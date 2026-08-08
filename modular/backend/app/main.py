from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .scenarios import (
    scenario1_portal_a2a,
    scenario2_foundry_af,
    scenario3a_hybrid_code_router,
    scenario3b_foundry_router_code_agent,
)


class ChatRequest(BaseModel):
    scenario: Literal["1", "2", "3a", "3b"]
    message: str = Field(min_length=1, max_length=4000)


class TraceStep(BaseModel):
    step: str
    detail: str


class ChatResponse(BaseModel):
    agent: str
    reply: str
    trace: list[TraceStep]


SCENARIOS = {
    "1": scenario1_portal_a2a.handle,
    "2": scenario2_foundry_af.handle,
    "3a": scenario3a_hybrid_code_router.handle,
    "3b": scenario3b_foundry_router_code_agent.handle,
}

app = FastAPI(title="A2A Foundry Switchboard", version="1.0.0")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> dict:
    try:
        return await SCENARIOS[request.scenario](request.message.strip())
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


frontend = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/static", StaticFiles(directory=frontend), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(frontend / "index.html")