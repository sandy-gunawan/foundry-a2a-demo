import os
from dataclasses import dataclass
from pathlib import Path

from azure.core.credentials import TokenCredential
from azure.identity import AzureCliCredential, ManagedIdentityCredential
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)


@dataclass(frozen=True)
class Settings:
    project_endpoint: str = os.getenv("PROJECT_ENDPOINT", "")
    model: str = os.getenv("MODEL", "gpt-5.4-mini")
    billing_agent: str = os.getenv("BILLING_AGENT", "agt-billing")
    billing_agent_version: str = os.getenv("BILLING_AGENT_VERSION", "1")
    tech_agent: str = os.getenv("TECH_AGENT", "agt-techsupport")
    tech_agent_version: str = os.getenv("TECH_AGENT_VERSION", "1")
    router_agent: str = os.getenv("ROUTER_AGENT", "agt-router")
    hybrid_router_agent: str = os.getenv("HYBRID_ROUTER_AGENT", "agt-hybrid-router")

    def require_project(self) -> None:
        if not self.project_endpoint:
            raise RuntimeError("PROJECT_ENDPOINT is required for this scenario.")


settings = Settings()


def azure_credential() -> TokenCredential:
    if os.getenv("IDENTITY_ENDPOINT") or os.getenv("MSI_ENDPOINT"):
        return ManagedIdentityCredential()
    return AzureCliCredential()