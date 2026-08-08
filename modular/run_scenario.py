"""Local runner for the pro-code scenarios (2 and 3a) against live Foundry agents."""

import asyncio
import sys

from backend.app.scenarios import (
    scenario2_foundry_af,
    scenario3a_hybrid_code_router,
)


HANDLERS = {
    "2": scenario2_foundry_af.handle,
    "3a": scenario3a_hybrid_code_router.handle,
}

MESSAGES = [
    "I was charged twice for invoice #4471.",
    "I can't log in, my password expired.",
]


async def main() -> None:
    scenario = sys.argv[1] if len(sys.argv) > 1 else "2"
    handler = HANDLERS[scenario]
    for message in MESSAGES:
        print(f"\nUSER [{scenario}]: {message}")
        result = await handler(message)
        print(f"  -> agent: {result['agent']}")
        print(f"  -> reply: {result['reply'][:300]}")


if __name__ == "__main__":
    asyncio.run(main())
