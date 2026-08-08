# A2A Foundry Modular Demo Handoff

## 0. What to build

Build a client-facing demo where a **router agent decides which of two specialist agents answers**, shown in three ways. Agents only reply with simple messages for now; the goal is to prove that a router agent can call other agents. Include newbie documentation, runnable code, and a real Azure deployment.

Build everything in `a2afoundry/modular/`.

## 1. Scenarios

1. **Portal A2A (low-code):** Foundry router agent plus two Foundry prompt agents via A2A.
2. **Pro-code on Foundry:** Python orchestrator using Microsoft Agent Framework; both specialists are Foundry agents.
3. **Hybrid:** build both variants:
   - **3a:** router in code using Agent Framework calls one Foundry agent and one in-code agent.
   - **3b:** router is a Foundry agent that calls one Foundry agent and one code agent exposed as an A2A server.

## 2. Agreed technology and environment

- Backend: Python FastAPI. Always use a `.venv` for Python.
- Frontend: professional HTML/CSS/JavaScript single page with one scenario switcher for `1`, `2`, `3a`, and `3b`; served by FastAPI.
- Primary deployment: Azure Container Apps. Also document VM, AKS, App Service, and Functions alternatives and when to use each.
- Preferred region: Southeast Asia.
- Preferred model: `gpt-5.4-mini`. Verify availability first; fall back to `gpt-4o-mini` in Southeast Asia, then East US 2.
- New resource group: `rg_a2a_foundry`; create the Foundry account, project, and model there.
- The user already ran `az login`.
- Provision real resources and deploy the runnable demo.
- Agents provide simple billing and technical-support replies, sufficient to demonstrate routing.

## 3. Verified implementation facts

### Microsoft Agent Framework for Python

Install `agent-framework`. Use `FoundryChatClient` with the Foundry project endpoint, model deployment name, and `AzureCliCredential` locally or `DefaultAzureCredential` in Azure Container Apps. Agent Framework supports Foundry, Azure OpenAI, A2A, workflows, agent-as-tool, and handoff patterns.

### Foundry A2A

- Connected Agents is the classic approach and is being deprecated. New Foundry recommends the A2A tool.
- Foundry visual workflows retire on 2026-12-01; use Agent Framework for pro-code orchestration.
- Enable incoming A2A with:
  - `PATCH {PROJECT_ENDPOINT}/agents/{name}?api-version=v1`
  - Include `agent_card` with `description`, `version`, and `skills`.
  - Include `agent_endpoint.protocol_configuration` with both `responses` and `a2a`.
- Foundry does not yet expose the complete incoming-A2A operation as a portal-only workflow.
- A2A endpoint: `{PROJECT_ENDPOINT}/agents/{agent}/endpoint/protocols/a2a`.
- Agent card: `{A2A_ENDPOINT}/agentCard/v1.0`.
- Authentication is Microsoft Entra only; API keys are not supported.
- The caller needs the **Foundry Agent Consumer** role on the project. Enabling A2A needs **Foundry User** or greater permissions.
- Create router-to-specialist connections with ARM `PUT .../connections/{name}?api-version=2025-04-01-preview` using:
  - `authType=AgenticIdentityToken`
  - `category=RemoteA2A`
  - `target=<A2A endpoint>`
  - `audience=https://ai.azure.com`
- For Foundry targets, do not append an agent-card path to the connection target.
- Attach each connection to a prompt agent using `A2APreviewTool(project_connection_id=connection.id)` and `PromptAgentDefinition` through `project.agents.create_version`.
- A2A v1.0 is recommended, JSON-RPC only, text-only, non-streaming, and preview.
- Prompt agents speak the responses protocol by default. Hosted agents are A2A-capable only when their code implements the responses protocol.
- Limits relevant to this demo: 120 connections per Foundry project and 128 tools per agent.

## 4. Target directory structure

```text
modular/
  README.md
  HANDOFF.md
  docs/
    00-overview.md
    01-scenario1-portal-a2a.md
    02-scenario2-procode-foundry.md
    03-scenario3-hybrid.md
    04-frontend-backend.md
    05-deploy-container-apps.md
    06-deploy-alternatives.md
  backend/
    app/
      main.py
      config.py
      scenarios/
        scenario1_portal_a2a.py
        scenario2_foundry_af.py
        scenario3a_hybrid_code_router.py
        scenario3b_foundry_router_code_agent.py
    requirements.txt
    .env.example
    Dockerfile
  frontend/
    index.html
    styles.css
    app.js
  codeagent/
    server.py
    requirements.txt
    Dockerfile
  infra/
    variables.example.ps1
    01-provision.ps1
    02-create-foundry-agents.py
    03-deploy-aca.ps1
```

## 5. Backend behavior

Expose `POST /api/chat` accepting `{scenario: "1"|"2"|"3a"|"3b", message: string}`. Every scenario module exposes `async handle(message)` and returns `{agent, reply, trace}` so all scenarios use the same frontend.

- **Scenario 1:** call the Foundry router through the Responses API with `agent_reference`; the router A2A-calls the selected specialist.
- **Scenario 2:** Agent Framework orchestrator with two Foundry specialists and code-owned routing.
- **Scenario 3a:** code router calls one Foundry specialist and one in-code specialist.
- **Scenario 3b:** Foundry router calls one Foundry specialist and the separately deployed code-agent A2A server.

## 6. Provisioning

`infra/01-provision.ps1` must:

1. Create `rg_a2a_foundry` in `southeastasia`.
2. Create a Foundry resource and project in that group.
3. Verify and deploy `gpt-5.4-mini`, falling back to `gpt-4o-mini` or East US 2 as documented.
4. Assign the development identity the Foundry User role.
5. Assign the application managed identity the Foundry Agent Consumer role, with retry guidance for RBAC propagation.

## 7. Azure Container Apps deployment

`infra/03-deploy-aca.ps1` must:

- Build the FastAPI backend image, which serves the API and frontend.
- Create an Azure Container Apps environment and externally accessible application with a system-assigned managed identity and scale range 1-3.
- Configure project endpoint, model, agent names, connection names, and code-agent A2A URL as environment variables.
- Deploy `codeagent/` as a second Container App.
- Feed its public A2A URL into the Scenario 3b connection.

## 8. Documentation requirements

Assume zero prior knowledge. Explain why before how, what each action creates, and who uses it. Use one consistent **company phone switchboard** analogy:

- router = operator
- specialists = departments
- agent card = directory entry
- A2A endpoint = extension
- connection = speed-dial
- Entra token = employee badge

Include exact portal menu paths and scripts, pitfalls, symptom-to-cause-to-fix tables, and Mermaid diagrams. Link to the existing parent documents instead of duplicating their foundational explanation.

## 9. Existing assets to adapt

Reuse and adapt:

- `../README.md`
- `../01-how-it-works.md`
- `../02-setup-step-by-step.md`
- `../03-use-cases.md`
- `../scripts/1-enable-a2a.ps1`
- `../scripts/2-create-connections.ps1`
- `../scripts/3-create-router.py`
- `../scripts/variables.example.ps1`

## 10. Build order and risks

Build in this order: docs and scaffold, provision, create Foundry agents, backend scenarios, frontend, Scenario 3b code agent, deploy, verify.

Primary risks:

- Verify `gpt-5.4-mini` availability in Southeast Asia before relying on it.
- Scenario 3b is the most preview-heavy; complete Scenarios 1, 2, and 3a first.
- Managed identity RBAC can take time to propagate; deployment and validation need retries.

## 11. Definition of done

- Provisioning lists the Foundry account and model deployment and confirms RBAC.
- Scenario 1 works in portal Chat and Traces show router-to-specialist transfer.
- Scenarios 2 and 3a run locally from `.venv` and route billing versus technical support correctly.
- Scenario 3b Traces show the Foundry router's A2A call to the Container Apps code agent.
- The deployed web application switches among all four modes and returns the expected specialist reply.

## 12. Required first actions

1. Confirm Southeast Asia and `gpt-5.4-mini` by checking availability.
2. Persist this handoff as `a2afoundry/modular/HANDOFF.md`.
3. Scaffold `a2afoundry/modular/`, `.venv`, and `.env.example`.
4. Run `infra/01-provision.ps1`.
5. Create Foundry prompt agents, enable A2A, and create connections.
6. Build the backend scenarios, frontend, code agent, deploy to Container Apps, and verify all scenarios.

All Python commands and package installations must use `.venv`.