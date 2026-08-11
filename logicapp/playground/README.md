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
Same Streamlit app, running in the cloud on a shareable URL. The Logic App URL is a
**configurable ACA secret** — change it anytime without rebuilding the image.

```powershell
# 1) Set the trigger URL (kept as a secret, never baked into the image)
$env:LOGIC_APP_URL = "<paste-your-trigger-URL>"

# 2) Build + deploy to rg_a2a_foundry (all names are overridable params)
pwsh -File .\deploy-aca.ps1
```
The script prints the public URL, e.g. `https://ca-logicapp-playground.<hash>.southeastasia.azurecontainerapps.io`.

Override any default if needed:
```powershell
pwsh -File .\deploy-aca.ps1 -ResourceGroup rg_a2a_foundry -Registry acra2asg0808x7q2 `
  -Environment acae-a2a-foundry -AppName ca-logicapp-playground
```

Change the Logic App URL later (no rebuild):
```powershell
az containerapp secret set -n ca-logicapp-playground -g rg_a2a_foundry --secrets logic-app-url="<new-url>"
az containerapp revision restart -n ca-logicapp-playground -g rg_a2a_foundry
```

### Configure the URL in the Azure portal (no CLI, no rebuild)
You can deploy first (even without setting `LOGIC_APP_URL` — it deploys with a
placeholder) and set the real URL in the portal so everyone using the public app
gets it:

1. **Azure portal** → open the Container App **`ca-logicapp-playground`**.
2. **Settings → Secrets** → add/edit a secret named **`logic-app-url`** → paste your
   trigger URL → **Save**. (Storing it as a *secret* hides the `sig=` value.)
3. **Application → Containers → Edit and deploy** → **Environment variables** →
   ensure **`LOGIC_APP_URL`** = **Reference a secret** → `logic-app-url` →
   **Save** (this creates a new revision).
4. The new revision restarts automatically. Anyone with the app's public URL can
   now chat — they all use the URL you configured.

> 🔓 The app has **external ingress and no sign-in**, so anyone with the URL can
> use it. That's fine for a shared demo; add authentication before real production.


## Try these
- `I was double charged on my last invoice` → routes to **agt-billing**
- `I can't log in to my account` → routes to **agt-techsupport**
- `What's the weather?` → **Default** fallback

## Notes
- These are for **testing/demo**, not production auth (anyone with the ACA URL can chat).
- Configuration is via **`LOGIC_APP_URL`**: env var / `.env` locally, ACA **secret** in the cloud.
