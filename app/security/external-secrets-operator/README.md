# external-secrets-operator

External Secrets Operator (ESO) synchronizes secrets from OpenBao into native Kubernetes `Secret` objects. Workloads consume standard Kubernetes Secrets while ESO handles the retrieval and rotation lifecycle transparently, keeping secret values out of Git.

## Role in the Stack

ESO sits between OpenBao (the secret store) and Kubernetes workloads. An `ExternalSecret` resource declares which OpenBao path to read; ESO reconciles it into a `Secret` that pods can mount or reference via environment variables.

```
ExternalSecret (CRD)
    └──► ESO controller ──► ClusterSecretStore (openbao)
                                └──► OpenBao KV v2 (kubernetes auth)
                                         └──► Kubernetes Secret ──► workload
```

The `ClusterSecretStore` named `openbao` authenticates to OpenBao using the Kubernetes auth engine: the ESO service account token is exchanged for a short-lived OpenBao token bound to the `external-secrets` role. This role must be configured in OpenBao (managed by vault-config-operator).

## Deployment

**Namespace**: `security`  
**Sync wave**: 1 (Helm chart), 3 (ClusterSecretStore)

```bash
helm upgrade --install external-secrets \
  oci://charts.external-secrets.io/external-secrets \
  --version 0.14.3 --namespace security -f values.yml
```

## Key Configuration

| Setting | Value |
|---|---|
| Version | 0.14.3 |
| CRDs | Installed and retained on uninstall |
| ClusterSecretStore name | `openbao` |
| OpenBao address | `http://openbao.openbao.svc.cluster.local:8200` |
| KV mount path | `secret` (v2) |
| Auth method | Kubernetes auth, role `external-secrets` |
| ESO service account | `external-secrets` in `security` |
| Controller CPU | 10–100m |
| Controller memory | 64–128Mi |
| Prometheus monitoring | Enabled |

## Using ExternalSecrets

Once deployed, reference the `openbao` ClusterSecretStore in any namespace:

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: my-app-secret
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: openbao
    kind: ClusterSecretStore
  target:
    name: my-app-secret
  data:
    - secretKey: password
      remoteRef:
        key: secret/my-app
        property: password
```

## Prerequisites

The OpenBao Kubernetes auth engine must be enabled and the `external-secrets` role must exist. This is managed by vault-config-operator.

## Resources

- [External Secrets Operator Documentation](https://external-secrets.io/latest/)
- [Vault Provider Reference](https://external-secrets.io/latest/provider/hashicorp-vault/)
- [Helm Chart values reference](https://github.com/external-secrets/external-secrets/blob/main/deploy/charts/external-secrets/values.yaml)
