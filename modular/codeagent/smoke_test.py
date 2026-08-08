"""Smoke test for the v0.3 code agent: fetch the card and send one message."""

import sys
import uuid

import httpx


def main() -> None:
    base = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8001").rstrip("/")
    card = httpx.get(f"{base}/.well-known/agent-card.json", timeout=30).json()
    print(f"CARD OK: name={card['name']!r} url={card['url']!r} protocol={card['protocolVersion']!r}")

    request = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": "My password expired and I am locked out."}],
                "messageId": str(uuid.uuid4()),
                "kind": "message",
            }
        },
    }
    body = httpx.post(f"{base}/", json=request, timeout=30).json()
    if "error" in body:
        raise SystemExit(f"A2A error: {body['error']}")
    text = " ".join(p.get("text", "") for p in body["result"]["parts"])
    print("REPLY:", text)
    print("ROUND-TRIP OK")


if __name__ == "__main__":
    main()
