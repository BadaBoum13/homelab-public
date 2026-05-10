# VictoriaMetrics

VictoriaMetrics is a fast, cost-efficient time-series database compatible with the Prometheus API. In this homelab it serves as the central storage for both metrics (via VMSingle, 365-day retention) and logs (via VLSingle, 10-day retention), replacing the need for separate Prometheus and Loki instances.

## Role in the Stack

VictoriaMetrics is the core of the observability stack:

```
kube-state-metrics ──┐
node-exporter      ──┼──► VMAgent ──► VMSingle (metrics, 365d)
ArgoCD / Grafana   ──┘
                                ▲
Vector (logs) ──────────────► VLSingle (logs, 10d)
                                ▲
VMAlert ──► VMAlertManager     Grafana reads both
```

**Custom Resources deployed** (in `crd/`):
- `VMSingle` — main metrics database (30Gi, 365-day retention)
- `VLSingle` — log database (30Gi, 10-day retention)
- `VMAgent` — metrics scraper (30s interval)
- `VMAlert` — alerting engine
- `VMAlertManager` — alert routing

## Dependencies

`prometheus-operator-crds` must be installed first (wave 0), as the VictoriaMetrics operator CRDs depend on it.

## Deployment

**Namespace**: `monitoring`  
**Sync wave**: 1 (operator CRDs), 2 (operator + custom resources), 3 (config CRs)

```bash
# Install prometheus-operator CRDs first (wave 0)
helm install prometheus-operator-crds oci://ghcr.io/prometheus-community/charts/prometheus-operator-crds \
  --namespace monitoring --create-namespace

# Install VictoriaMetrics operator CRDs (wave 1)
helm repo add vm https://victoriametrics.github.io/helm-charts/
helm install victoriametrics-operator-crds vm/victoria-metrics-operator-crds \
  -n monitoring --create-namespace

# Install VictoriaMetrics operator (wave 2)
helm install victoriametrics-operator vm/victoria-metrics-operator \
  -f values.yaml -n monitoring

# Apply custom resources (wave 3)
kubectl apply -f crd/
```

## Key Configuration

| Setting | Value |
|---|---|
| Metrics retention | 365 days |
| Metrics storage | 30Gi on `longhorn-ssd` |
| Logs retention | 10 days |
| Logs storage | 30Gi on `longhorn-ssd` |
| Scrape interval | 30s |
| Operator CPU | 100m req/limit |
| Operator Memory | 128Mi req/limit |

## Resources

- [VictoriaMetrics Documentation](https://docs.victoriametrics.com/)
- [VictoriaMetrics Helm Charts](https://github.com/VictoriaMetrics/helm-charts)
- [Helm Chart values reference](https://github.com/VictoriaMetrics/helm-charts/blob/master/charts/victoria-metrics-operator/values.yaml)
