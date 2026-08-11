# Foundry Router — Playground

Two lightweight ways to chat with the Logic App (from
[`../Build-Logic-App-Foundry-Router.md`](../Build-Logic-App-Foundry-Router.md)).
Both call the Logic App **server-side / non-browser**, so there is **no CORS** issue.

> 🔐 The trigger URL contains a secret `sig=...`. Keep it in a local `.env`
> (gitignored) or an environment variable — never commit it.

## Get your trigger URL
Logic App → open the **When an HTTP request is received** trigger → copy the **HTTP URL**
(only appears after Publish).

Then either set an env var:
```powershell
$env:LOGIC_APP_URL = "<paste-your-trigger-URL>"
```
or copy `.env.example` → `.env` and paste the URL there.

---

## Option 1 — Terminal playground (`chat.ps1`)
Zero dependencies. Instant.
```powershell
$env:LOGIC_APP_URL = "<paste-your-trigger-URL>"   # or use .env
pwsh -File .\chat.ps1
```
Type a message; press Enter. `exit` to quit.

---

## Option 2 — Streamlit chat UI (`playground.py`)
A Foundry-playground-style chat page, running locally.
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # then edit .env and paste your URL
streamlit run playground.py
```
Opens a browser chat page. The URL stays in `.env`, never in the page.

---

## Try these
- `I was double charged on my last invoice` → routes to **agt-billing**
- `I can't log in to my account` → routes to **agt-techsupport**
- `What's the weather?` → **Default** fallback

## Notes
- These are for **testing/demo**, not production auth.
- A browser-hosted **web** version (deployable to Azure Container Apps) lives in
  [`../webapp/`](../webapp/) once created.
