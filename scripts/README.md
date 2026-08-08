# Scripts — run in this order

These scripts build the **router + 2 specialists** system. They implement the
parts of the guide that the Foundry **portal can't do yet** (enabling A2A) using
the REST API and Python SDK. All values come from `variables.ps1`.

| Order | File | Guide step | What it does (analogy) |
|---|---|---|---|
| 0 | `variables.example.ps1` → copy to `variables.ps1` | — | Your names/IDs in one place |
| 1 | `1-enable-a2a.ps1` | Part A / A3 | Publishes both departments' **extensions** + nameplates |
| 2 | `2-create-connections.ps1` | Part B / B1 | Saves two **speed‑dials** for the router |
| 3 | `3-create-router.py` | Part B / B2 + Part C | Hires the **operator**, adds transfer buttons, tests routing |

## Run it

```powershell
# 0) one-time: create your variables file and edit it
Copy-Item .\variables.example.ps1 .\variables.ps1
notepad .\variables.ps1

# sign in (get your Entra badge)
az login

# 1) publish A2A on both specialists
.\1-enable-a2a.ps1

# 2) create the two A2A connections (speed-dials)
.\2-create-connections.ps1

# 3) build the router + run the routing test  (Python)
pip install "azure-ai-projects>=2.3.0" azure-identity
python .\3-create-router.py
```

## Before you run

- The **two specialist agents** (`agt-billing`, `agt-techsupport`) must already
  exist as **prompt agents** (create them in the portal — guide Step A1).
- You need `az login` and the **Foundry User** role to enable A2A, plus
  **Foundry Agent Consumer** for the calling identity (guide Step B3).

## Notes / gotchas (verified from Microsoft docs)

- A2A auth is **Entra only** — the connection uses `AgenticIdentityToken`, never
  an API key.
- A2A here is **text‑only**, **no streaming**, and **preview** — fine for pilots.
- Each connection counts toward the project's **120‑connection** limit — reuse
  one connection per specialist instead of creating duplicates.
- If `1-enable-a2a.ps1` returns a version/api error, your tenant may expect a
  different `api-version`; try `2025-11-15-preview` in the PATCH URL.
