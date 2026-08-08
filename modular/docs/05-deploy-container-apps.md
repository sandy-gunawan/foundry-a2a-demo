# 05 - Deploy to Azure Container Apps

Container Apps runs containers without requiring you to manage virtual machines or Kubernetes nodes. This demo deploys two apps: the FastAPI switchboard and the custom A2A Tech Support server.

## Resources created

| Resource | Name | Who uses it |
|---|---|---|
| Resource group | `rg_a2a_foundry` | Holds the demo lifecycle |
| Container Registry | `<your-registry>` | Stores both images |
| Container Apps environment | `acae-a2a-foundry` | Shared runtime boundary |
| Web app | `ca-a2a-switchboard` | Demo users |
| Code agent | `ca-a2a-codeagent` | Scenario 3b Foundry router |

## Step 1 - Build images remotely

Run `infra/03-deploy-aca.ps1`. Azure Container Registry builds each Dockerfile from the modular folder.

**This creates:** immutable container image layers used by Container Apps revisions.

> **Switchboard analogy:** package the operator desk and remote department before delivering them to their offices.
>
> **Risk this prevents:** local Docker configuration does not affect the Azure build.

## Step 2 - Deploy the code agent first

The script deploys port `8001`, reads the assigned HTTPS hostname, then updates `A2A_PUBLIC_URL`.

**This creates:** the real extension needed before the hybrid router can save its speed-dial.

**Verify:** open `https://CODE_FQDN/.well-known/agent-card.json`.

> **Switchboard analogy:** install and test the remote extension before programming it into the operator's phone.
>
> **Risk this prevents:** a connection cannot target an address that does not exist yet.

## Step 3 - Wire the hybrid router

The deployment script reruns `02-create-foundry-agents.py --code-agent-url ...`, creates the no-auth connection, and creates `agt-hybrid-router`.

**Verify:** Foundry → **Build → Agents → agt-hybrid-router → Chat**, then **Traces**.

> **Switchboard analogy:** save the newly assigned extension as a speed-dial.

## Step 4 - Deploy FastAPI and assign identity

The script enables a system-assigned managed identity and grants it **Foundry Agent Consumer** at project scope using role ID `eed3b665-ab3a-47b6-8f48-c9382fb1dad6`.

**This creates:** keyless least-privilege access from FastAPI to agent endpoints.

> **Switchboard analogy:** the operator receives a badge that opens the call room but cannot redesign the building.
>
> **Risk this prevents:** missing RBAC causes `403`; API keys would grant broader access and require secret rotation.

## Final validation

1. Open the printed `https://BACKEND_FQDN` URL.
2. Select each scenario.
3. Send one billing and one login request.
4. Confirm the displayed answering agent.
5. Confirm Scenarios 1 and 3b in Foundry **Traces**.

RBAC can take several minutes to propagate. If the first request returns `403`, wait briefly and retry; do not replace managed identity with a key.

---

## 🐛 Real deployment issues (from an actual deploy) and how we solved them

These are the exact problems hit while standing up the code agent for Scenario 3b,
in the order they appeared. The A2A protocol detail has the full write-up in
[Scenario 3 → the big one](03-scenario3-hybrid.md#-the-big-one-a2a-protocol-version-v03-vs-v10).

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 1 | `az acr build` prints a long Python traceback ending in `UnicodeEncodeError: 'charmap' codec can't encode … cp1252` and **exits 1** | Windows CLI **log-streaming** bug (colorama vs pip's Unicode output) — **not** a build failure | Ignore the exit code; the image is pushed. Verify with `az acr repository show-tags --name $CONTAINER_REGISTRY --repository a2a-codeagent -o tsv` |
| 2 | Agent card keeps showing `http://127.0.0.1:8001` even after `--set-env-vars A2A_PUBLIC_URL=…` | The **original revision** (created without the env var) was still the active one | Force a **new revision**: `az containerapp update … --revision-suffix v03 --set-env-vars "A2A_PUBLIC_URL=$url"` |
| 3 | Foundry router: `Failed to resolve agent card … A2A.V0_3.AgentCard missing 'url','protocolVersion','preferredTransport'` | Code agent served an A2A **v1.0** card; Foundry's A2A tool wants **v0.3** for custom endpoints | Serve a **v0.3** card + `message/send` — we hand-rolled `codeagent/server.py` in plain Starlette |
| 4 | Card is reachable from your laptop but Foundry still can't fetch it | Container App **ingress is internal** | Deploy with `--ingress external` (Foundry calls it from the cloud) |
| 5 | Which auth type for a public, no-auth code agent? | Unclear whether Foundry accepts anonymous | **`authType: None` works** (HTTP 200) — see `infra/03b-wire-hybrid.py` |

> ⚠️ **Caution — the all-in-one `infra/03-deploy-aca.ps1` vs a manual portal setup.**
> If you created your agents/connections **manually in the portal** (as in the
> Scenario 1 walkthrough), do **not** run the full script afterward: it recreates
> the billing/tech/router agents and connections with a different auth type and can
> break your working wiring. For Scenario 3b on top of a manual setup, use the
> **focused steps** in [Scenario 3](03-scenario3-hybrid.md#deploy-scenario-3b-real-verified-steps),
> which reuse your existing `conn-billing`.

> 🧠 **Why `--revision-suffix` matters:** Container Apps bakes environment variables
> into a **revision**. A container reads `A2A_PUBLIC_URL` **once at startup**, so an
> env change only takes effect on a **new** revision — updating the template alone
> won't change what the already-running container serves.