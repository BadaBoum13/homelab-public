# vault-config-operator

vault-config-operator (VCO) manages OpenBao configuration declaratively via Kubernetes CRDs. Instead of running `bao` CLI commands after each restart or maintaining imperative scripts, configuration is expressed as Kubernetes resources and reconciled continuously by the operator.

## Role in the Stack

VCO bridges Kubernetes and OpenBao: it reads CRD resources from the cluster and applies the corresponding configuration to OpenBao. This enables GitOps-driven secret engine and auth engine management.

```
Git (CRD manifests)
    └──► ArgoCD ──► Kubernetes CRDs (VaultAuthEngineMount, Policy, KubernetesAuthEngineRole…)
                        └──► vault-config-operator ──► OpenBao API
                                                           └──► auth engines, policies, roles configured
```

VCO is responsible for bootstrapping the Kubernetes auth engine that External Secrets Operator uses to authenticate with OpenBao.

## Managed Resources

| CRD | Purpose |
|---|---|
| `VaultAuthEngineMount` | Enable/configure auth engines (e.g., Kubernetes) |
| `KubernetesAuthEngineConfig` | Configure Kubernetes auth with cluster API URL and CA |
| `KubernetesAuthEngineRole` | Bind service accounts to OpenBao policies |
| `SecretEngineMount` | Enable secret engines (e.g., KV v2) |
| `Policy` | Define OpenBao ACL policies |
| `VaultSecret` | Write static secrets into OpenBao from Kubernetes |

## Deployment

**Namespace**: `security`  
**Sync wave**: 1

```bash
helm repo add vault-config-operator https://redhat-cop.github.io/vault-config-operator
helm upgrade --install vault-config-operator \
  vault-config-operator/vault-config-operator \
  --version 0.9.4 --namespace security -f values.yml
```

## Key Configuration

| Setting | Value |
|---|---|
| Version | 0.9.4 |
| OpenBao address | `http://openbao.openbao.svc.cluster.local:8200` |
| Namespace | `security` |
| CPU | 10–200m |
| Memory | 64–128Mi |
| Prometheus monitoring | Enabled |

## Example: ESO Bootstrap

The following CRDs configure the Kubernetes auth engine so that External Secrets Operator can authenticate with OpenBao:

```yaml
# Enable Kubernetes auth engine
apiVersion: redhatcop.redhat.io/v1alpha1
kind: VaultAuthEngineMount
metadata:
  name: kubernetes
spec:
  path: kubernetes
  type: kubernetes
---
# Configure the Kubernetes auth engine
apiVersion: redhatcop.redhat.io/v1alpha1
kind: KubernetesAuthEngineConfig
metadata:
  name: kubernetes
spec:
  path: kubernetes
  tokenReviewerServiceAccount:
    name: vault-config-operator
    namespace: security
---
# Create the external-secrets role
apiVersion: redhatcop.redhat.io/v1alpha1
kind: KubernetesAuthEngineRole
metadata:
  name: external-secrets
spec:
  path: kubernetes
  policies:
    - external-secrets-readonly
  targetServiceAccounts:
    - name: external-secrets
      namespace: security
  TTL: 1h
```

## Resources

- [vault-config-operator Documentation](https://github.com/redhat-cop/vault-config-operator)
- [CRD Reference](https://github.com/redhat-cop/vault-config-operator/tree/master/docs)
- [Helm Chart values reference](https://github.com/redhat-cop/vault-config-operator/blob/master/helm/vault-config-operator/values.yaml)
