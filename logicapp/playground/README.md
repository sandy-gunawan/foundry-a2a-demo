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

---

## Option 3 — Host `playground.py` on Azure Container Apps
Same Streamlit app, running in the cloud on a shareable URL. You set the Logic App
URL **inside the app** (⚙️ Settings sidebar) — no env var, no secret, no redeploy.

```powershell
# Build + deploy to rg_a2a_foundry (all names are overridable params)
pwsh -File .\deploy-aca.ps1
```
The script prints the public URL, e.g. `https://ca-logicapp-playground.<hash>.southeastasia.azurecontainerapps.io`.

Override any default if needed:
```powershell
pwsh -File .\deploy-aca.ps1 -ResourceGroup rg_a2a_foundry -Registry acra2asg0808x7q2 `
  -Environment acae-a2a-foundry -AppName ca-logicapp-playground
```

### Set the URL (no CLI, no portal, no redeploy)
1. Open the app's public URL.
2. In the **⚙️ Settings** sidebar (use the top-left **›** to expand it), paste your
   Logic App trigger URL → **Save URL**.
3. It's stored on the server and shared by everyone using the page — start chatting.

> 🔓 The app has **external ingress and no sign-in**, so anyone with the URL can use
> it (and can see/replace the configured Logic App URL). Fine for a shared demo; add
> authentication before real production. The saved URL resets if the container
> restarts/redeploys — just paste it again.


## Try these
- `I was double charged on my last invoice` → routes to **agt-billing**
- `I can't log in to my account` → routes to **agt-techsupport**
- `What's the weather?` → **Default** fallback

## Notes
- These are for **testing/demo**, not production auth (anyone with the ACA URL can chat).
- Configuration: local runs use `LOGIC_APP_URL` (env/`.env`); the deployed app is
  configured from its **⚙️ Settings sidebar** (stored server-side, shared by all users).
