# cert-manager

cert-manager is a Kubernetes-native certificate controller. It automates the issuance and renewal of TLS certificates from Let's Encrypt, eliminating the need to manage certificates manually. In this homelab it uses CloudFlare DNS01 challenge validation so that certificates can be issued for any domain without requiring a publicly reachable HTTP endpoint.

## Role in the Stack

cert-manager sits between Traefik (which needs TLS certificates) and Let's Encrypt (which issues them). Every ingress in the cluster references the `cloudflare` ClusterIssuer, which cert-manager uses to perform DNS01 validation via the CloudFlare API.

```
Ingress (annotation: cert-manager.io/cluster-issuer: cloudflare)
    └──► cert-manager ──► Let's Encrypt ACME ──► CloudFlare DNS01 ──► certificate issued
                                                      └──► Secret in namespace ──► Traefik TLS
```

## Deployment

**Namespace**: `security`  
**Sync wave**: 1

```bash
# Install CRDs
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.18.2/cert-manager.crds.yaml

# Install cert-manager
helm upgrade --install cert-manager \
  oci://quay.io/jetstack/charts/cert-manager \
  --version v1.18.2 --namespace security -f values.yml
```

## Key Configuration

| Setting | Value |
|---|---|
| Version | v1.18.2 |
| ACME solver | CloudFlare DNS01 |
| ClusterIssuer name | `cloudflare` |
| CRDs | Enabled and retained on uninstall |
| CPU | 10–256m |
| Memory | 64–128Mi |
| Log level | 2 (info) |
| Prometheus monitoring | Enabled |

## Resources

- [cert-manager Documentation](https://cert-manager.io/docs/)
- [CloudFlare DNS01 solver](https://cert-manager.io/docs/configuration/acme/dns01/cloudflare/)
- [Helm Chart values reference](https://github.com/cert-manager/cert-manager/blob/main/deploy/charts/cert-manager/values.yaml)
