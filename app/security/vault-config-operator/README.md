# vault-config-operator

Vault Config Operator is the declarative configuration layer for OpenBao. It lets the cluster manage Vault/OpenBao auth engines, policies, roles, and secret engine settings as Kubernetes resources so each application can own and manage its own scoped access instead of sharing a single central secret admin workflow.

## Role in the Stack

OpenBao is the backing secret store. vault-config-operator configures the server side so workloads can authenticate to OpenBao through Kubernetes auth and use app-specific policies and roles without manual CLI configuration.

```text
OpenBao (openbao namespace)
    └──► vault-config-operator (security namespace)
            ├──► auth engines
            ├──► policies
            ├──► roles
            └──► secret engine configuration
```

## Deployment

**Namespace**: `security`  
**Sync wave**: 2

```bash
helm repo add redhat-cop https://redhat-cop.github.io/vault-config-operator
helm repo update redhat-cop
helm upgrade --install vault-config-operator redhat-cop/vault-config-operator \
  --namespace security \
  -f values.yml \
  --create-namespace --wait
```

## Key Configuration

| Setting | Value |
|---|---|
| Chart | `redhat-cop/vault-config-operator` |
| Version | `v0.8.51` |
| Namespace | `security` |
| Vault address | `http://openbao.openbao.svc.cluster.local:8200` |
| Metrics | Enabled |
| Webhook / TLS certs | Chart-managed self-signed certs |
| Certificate manager | Disabled (`enableCertManager: false`) |

## Prerequisites

The operator expects OpenBao to already be present and reachable. The Kubernetes auth method must be enabled and a service account in the `security` namespace must be authorized to authenticate to OpenBao for operator reconciliation.

This is the component that configures the OpenBao auth backend, policy bindings, and app-scoped roles used by the rest of the stack.

## Resources

- [Vault Config Operator GitHub](https://github.com/redhat-cop/vault-config-operator)
- [Vault Config Operator Helm chart](https://github.com/redhat-cop/vault-config-operator/tree/main/config/helmchart)
- [OpenBao documentation](https://openbao.org/docs/)
