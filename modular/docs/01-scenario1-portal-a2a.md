# 01 - Scenario 1: Portal A2A

This mode stores the operator and both departments in Microsoft Foundry. The portal creates the prompt agents; the script performs the A2A operations that the portal does not fully expose.

## Step 1 - Create the Foundry resource and project

**Why:** agents need one security and management boundary.

**Portal:** Azure portal → **Create a resource** → **Microsoft Foundry** → create account `<your-account>` in resource group `rg_a2a_foundry`, region **Southeast Asia**. In Foundry → **Operate → Admin → New project**, create `proj-a2a-modular`.

**Script:** run `infra/01-provision.ps1`.

**This creates:** the account, project, and `gpt-5.4-mini` deployment used by every agent.

**Verify:** Foundry → **Build → Models** shows the deployment.

> **Switchboard analogy:** this creates the office and installs the internal phone system.
>
> **Risk this prevents:** agents created in different projects cannot share the intended project connections.

## Step 2 - Hire the departments

**Portal:** Foundry → **Build → Agents → New agent**. Create `agt-billing` and `agt-techsupport`, choose `gpt-5.4-mini`, and use the instructions from `infra/02-create-foundry-agents.py`.

**Script equivalent:** the Python script creates both versions automatically.

**This creates:** two versioned prompt agents used by all scenarios.

**Verify:** open each agent's **Chat** and send a matching request.

> **Switchboard analogy:** Billing and Tech Support are hired and given distinct job sheets.
>
> **Risk this prevents:** overlapping descriptions make the operator transfer calls inconsistently.

## Step 3 - Publish the two extensions

**Why:** a prompt agent cannot receive A2A calls until its A2A protocol and card are enabled.

**Portal:** an agent's **Details** page may show **Create an agent card to set up A2A**, but the complete protocol operation still requires REST or SDK.

**Script:** `infra/02-create-foundry-agents.py` PATCHes each agent and then creates the connections.

**This creates:** an agent card and A2A endpoint for each specialist.

**Verify:** request:

```text
https://<your-account>.services.ai.azure.com/api/projects/proj-a2a-modular/agents/agt-billing/endpoint/protocols/a2a/agentCard/v1.0
```

Use an Entra token for audience `https://ai.azure.com`.

> **Switchboard analogy:** publishing the card lists each extension in the company directory.
>
> **Risk this prevents:** an unpublished extension returns `404`.

## Step 4 - Save speed-dials and create the operator

The script creates `conn-billing` and `conn-techsupport` with `RemoteA2A`, `AgenticIdentityToken`, and audience `https://ai.azure.com`. It attaches both connections to `agt-router` as `A2APreviewTool` tools.

**Portal location:** Foundry → **Operate → Admin → Connected resources** shows the connections. Foundry → **Build → Agents → agt-router** shows the router.

**This creates:** reusable authenticated speed-dials and the Scenario 1 operator.

**Verify:** router **Chat** handles one billing and one login request. Open **Traces** and confirm one specialist A2A call per request.

> **Switchboard analogy:** the operator gets two badge-protected speed-dials.
>
> **Risk this prevents:** key authentication does not work for Foundry-to-Foundry A2A.

## Required roles

| Identity | Role | Scope | Purpose |
|---|---|---|---|
| Developer | Foundry User | Project | Create and test agents |
| Connection creator | Foundry Project Manager or higher | Project/account | Create A2A project connections |
| Calling application | Foundry Agent Consumer | Project | Invoke agent endpoints only |

Scripts use stable role IDs because Foundry role names were recently renamed.