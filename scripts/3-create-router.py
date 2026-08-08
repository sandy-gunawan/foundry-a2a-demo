"""
3-create-router.py
-------------------------------------------------------------------
PART B / Step B2 (+ Part C test) — Build the ROUTER agent and test it.

WHAT THIS DOES (switchboard analogy):
    Hires the OPERATOR (router agent) and gives it a TRANSFER BUTTON
    (the A2A tool) wired to the two SPEED-DIALS (connections) you made
    in step B1. Then it makes two test calls to prove routing works.

WHY PYTHON (verified from Microsoft docs):
    The A2A *tool* on the caller side is added via the SDK's
    A2APreviewTool, referencing each connection's id.

PREREQS:
    pip install "azure-ai-projects>=2.3.0" azure-identity
    az login   (so DefaultAzureCredential can get your Entra badge)
    Steps A3 and B1 already done.
    Router identity has the "Foundry Agent Consumer" role (Step B3).

EDIT the CONFIG block below to match your variables.ps1 values.
-------------------------------------------------------------------
"""

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, A2APreviewTool

# ================== CONFIG (match your variables.ps1) ==================
PROJECT_ENDPOINT = "https://foundryfull.services.ai.azure.com/api/projects/proj-demo-sea-001"
MODEL            = "gpt-5.4-mini"
ROUTER_AGENT     = "agt-router"
BILLING_CONN     = "conn-billing"       # speed-dial to Billing
TECH_CONN        = "conn-techsupport"   # speed-dial to Tech Support
# ======================================================================

# The operator's job description. NOTE: no if/else code — the model routes
# by reading each specialist's agent-card description.
ROUTER_INSTRUCTIONS = (
    "You are a switchboard router. Do NOT answer questions yourself.\n"
    "Delegate each request to exactly one connected specialist agent:\n"
    "- Billing agent: invoices, payments, refunds, duplicate or wrong charges.\n"
    "- Tech Support agent: logins, password resets, lockouts, error messages.\n"
    "If the request is unclear, ask ONE short clarifying question first "
    "(e.g. 'Is this about a charge or about logging in?').\n"
    "Return the specialist's answer to the user."
)

def main() -> None:
    credential = DefaultAzureCredential()
    project = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=credential)
    openai = project.get_openai_client()

    # Resolve the two speed-dials (connections) to their ids
    billing_conn = project.connections.get(BILLING_CONN)
    tech_conn = project.connections.get(TECH_CONN)

    # One A2A "transfer button" per speed-dial
    tools = [
        A2APreviewTool(project_connection_id=billing_conn.id),
        A2APreviewTool(project_connection_id=tech_conn.id),
    ]

    # Create (or update) the router as a prompt agent with the two A2A tools
    agent = project.agents.create_version(
        agent_name=ROUTER_AGENT,
        definition=PromptAgentDefinition(
            model=MODEL,
            instructions=ROUTER_INSTRUCTIONS,
            tools=tools,
        ),
    )
    print(f"Router created: name={agent.name} version={agent.version}")

    # ---- Part C: test routing with two messages ----
    tests = [
        "I was charged twice for invoice #4471.",   # -> should reach Billing
        "I can't log in, it says my password expired.",  # -> should reach Tech Support
    ]
    for question in tests:
        print(f"\nUSER: {question}")
        response = openai.responses.create(
            input=question,
            extra_body={
                "agent_reference": {"name": agent.name, "type": "agent_reference"}
            },
        )
        print(f"ROUTER: {response.output_text}")

    print("\nDone. Open the router's Traces tab to confirm each call went to the "
          "expected specialist (Billing vs Tech Support).")

if __name__ == "__main__":
    main()
