# ArgoCD

ArgoCD is a declarative GitOps continuous delivery platform for Kubernetes. It watches this Git repository and automatically reconciles the cluster state to match what is declared here, with self-healing and auto-pruning enabled.

## Role in the Stack

ArgoCD is the entry point for all application deployments. Every other application in this homelab is managed as an ArgoCD `Application` resource. A single bootstrap application (`app/argocd-bootstrap.yaml`) is applied manually once; it then discovers and deploys all other ArgoCD application manifests automatically (app-of-apps pattern).

**Sync waves** control deployment ordering — see the root [README](../../README.md#deployment-order-argocd-sync-waves) for the full sequence.

## Deployment

**Namespace**: `argocd`  
**Method**: Helm, managed by ArgoCD itself after bootstrapping

```bash
# Apply CRDs
kubectl apply -k https://github.com/argoproj/argo-cd/manifests/crds?ref=stable

# Add Helm repo and install
helm repo add argo https://argoproj.github.io/argo-helm
helm install argocd argo/argo-cd -n argocd --create-namespace -f values.yml

# Let ArgoCD manage itself and all other apps
kubectl apply -f ../../argocd-bootstrap.yaml
```

## Key Configuration

| Setting | Value |
|---|---|
| URL | `https://argocd.biduleproofzone.ovh` |
| Replicas | 1 (server, controller, repoServer, applicationSet) |
| Redis | Enabled (128Mi memory limit) |
| Ingress | Traefik + cert-manager (CloudFlare issuer) |
| Metrics | ServiceMonitor enabled (scraped by VictoriaMetrics) |
| Notifications | Enabled |
| Server CPU | 50–100m |
| Server Memory | 64–128Mi |
| Controller CPU | 250–500m |
| Controller Memory | 256–512Mi |

All applications are configured with `automated.prune: true` and `automated.selfHeal: true`.

## Access

- **URL**: `https://argocd.biduleproofzone.ovh`
- **Credentials**: managed via Kubernetes secret in the `argocd` namespace

## TODO

- Add SSO
- Add repository integration

## Resources

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Helm Chart values reference](https://github.com/argoproj/argo-helm/blob/main/charts/argo-cd/values.yaml)
