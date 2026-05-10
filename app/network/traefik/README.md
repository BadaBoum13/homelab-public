# Traefik

Traefik is a cloud-native reverse proxy and ingress controller. In this homelab it is bundled with K3s and configured via a `HelmChartConfig` resource — no separate Helm install is needed. All HTTP traffic is globally redirected to HTTPS.

## Role in the Stack

Traefik is the single entry point for all external traffic into the cluster. Every application that exposes a web UI uses a Kubernetes `Ingress` resource with `ingressClassName: traefik`. TLS termination is handled by cert-manager certificates attached to each ingress.

```
Internet ──► Traefik ──► (HTTP 301) ──► HTTPS
                    └──► Ingress rules ──► ArgoCD / Grafana / Longhorn / Nextcloud
```

## Deployment

**Namespace**: `kube-system` (bundled with K3s)  
**Method**: `HelmChartConfig` CRD — K3s reads this resource and applies it to its bundled Traefik Helm release  
**Sync wave**: 3 (config applied after infra is ready)

No manual Helm install is required. Applying the `HelmChartConfig` manifest is enough:

```bash
kubectl apply -f app/network/traefik/
```

## Key Configuration

| Setting | Value |
|---|---|
| HTTP → HTTPS redirect | Global (all ingresses) |
| Ingress class | `traefik` |
| TLS | Managed by cert-manager per ingress |

## Resources

- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [K3s HelmChartConfig](https://docs.k3s.io/helm#customizing-packaged-components-with-helmchartconfig)
