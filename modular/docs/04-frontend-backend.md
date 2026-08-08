# 04 - Frontend and Backend

## Why one API contract

The browser should demonstrate routing, not contain routing logic. It always calls `POST /api/chat`; FastAPI selects a scenario handler and each handler returns `agent`, `reply`, and `trace`.

> **Switchboard analogy:** callers use one main phone number even when the company replaces the equipment behind it.

## FastAPI routes

| Route | Purpose | Used by |
|---|---|---|
| `GET /` | Serve the single-page interface | Browser |
| `GET /static/*` | Serve CSS and JavaScript | Browser |
| `GET /api/health` | Confirm the process is running | Operators and health checks |
| `POST /api/chat` | Route one message | Browser and tests |

Input is limited to 4,000 characters. The UI inserts replies with `textContent`, not HTML, so agent output cannot inject markup.

## Configuration

Copy `backend/.env.example` to `backend/.env`. Environment variables are configuration, while credentials come from identity:

- Local: `AzureCliCredential` uses the current `az login` session.
- Container Apps: `ManagedIdentityCredential` uses the app's system-assigned identity.

No API key is stored in source or Container Apps settings.

## Local verification

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.app.main:app --reload
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

Expected result: `status` is `ok`. Then open `http://127.0.0.1:8000` and test all available scenarios.

> **Switchboard analogy:** the health route proves the main number answers; a chat request proves the operator can complete a transfer.