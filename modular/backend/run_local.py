"""Run one scenario's handler locally against the configured Foundry agents.

Usage: python backend/run_local.py 2
"""

import asyncio
import sys

from backend.app.scenarios import (
    scenario1_portal_a2a,
    scenario2_foundry_af,
    scenario3a_hybrid_code_router,
    scenario3b_foundry_router_code_agent,
)

HANDLERS = {
    "1": scenario1_portal_a2a.handle,
    "2": scenario2_foundry_af.handle,
    "3a": scenario3a_hybrid_code_router.handle,
    "3b": scenario3b_foundry_router_code_agent.handle,
}

QUESTIONS = [
    "I was charged twice for invoice #4471.",
    "I can't log in, my password expired.",
]


async def main() -> None:
    scenario = sys.argv[1] if len(sys.argv) > 1 else "2"
    handle = HANDLERS[scenario]
    print(f"=== Scenario {scenario} ===")
    for question in QUESTIONS:
        print(f"\nUSER: {question}")
        result = await handle(question)
        print(f"AGENT ({result['agent']}): {result['reply']}")
        for step in result["trace"]:
            print(f"  - {step['step']}: {step['detail']}")


if __name__ == "__main__":
    asyncio.run(main())
