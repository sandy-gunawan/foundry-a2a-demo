# 06 - Deployment Alternatives

Azure Container Apps is the primary choice because this demo has two HTTP containers, needs public HTTPS ingress, and does not need cluster administration.

| Host | Choose it when | Trade-off for this demo |
|---|---|---|
| Azure VM | You require operating-system control or legacy software | You patch the OS, configure `systemd`, TLS proxy, firewall, and scaling |
| AKS | A platform team already operates Kubernetes or you need advanced networking/policy | Most control and portability, but highest operational overhead |
| App Service | You want a conventional single web app with deployment slots | Excellent for FastAPI; the second A2A service still needs another app and configuration |
| Azure Functions | Work is short, event-driven, and naturally stateless | A2A HTTP tasks and Agent Framework sessions need careful timeout and state design |

## VM shape

Run Uvicorn under `systemd`, put Nginx in front on port `443`, assign a managed identity to the VM, and grant Foundry Agent Consumer. Deploy the code agent as a second service on a private local port.

> **Switchboard analogy:** you own the office, wiring, locks, and repairs.

## AKS shape

Create two Deployments, two Services, and one ingress controller. Use Microsoft Entra Workload ID for the backend service account. Add readiness probes for `/api/health` and the code-agent card.

> **Switchboard analogy:** a building manager can move many departments between rooms, but someone must operate the building.

## App Service shape

Create two Linux Web Apps or one web app plus Container Apps for the code agent. Enable managed identity on the FastAPI app and configure the same environment variables.

> **Switchboard analogy:** rent serviced offices; the landlord handles the building while you manage each department.

## Functions shape

Use an HTTP trigger for `/api/chat`, but store durable conversation state externally and verify execution timeout against worst-case agent latency. A separate always-on A2A host is usually clearer for Scenario 3b.

> **Switchboard analogy:** call in temporary staff for each request; do not assume they keep notes after the call ends.

## Recommendation

Stay with Container Apps for this demonstration. Move to AKS only when cluster-level controls are a real requirement, to App Service when the system becomes one conventional web app, or to Functions when requests become event-driven and short-lived.