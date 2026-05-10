# kube-state-metrics

kube-state-metrics is a service that listens to the Kubernetes API and generates metrics about the state of Kubernetes objects (deployments, pods, nodes, PVCs, etc.). It exposes these metrics in Prometheus format for VictoriaMetrics to scrape.

## Role in the Stack

kube-state-metrics fills the gap between node-level metrics (provided by node-exporter) and application-level metrics — it answers questions like "how many pods are in a CrashLoopBackOff?" or "is this PVC bound?".

```
Kubernetes API ──► kube-state-metrics ──► VMAgent ──► VMSingle ──► Grafana
```

## Deployment

**Namespace**: `monitoring`  
**Sync wave**: 2

```bash
helm upgrade --install kube-state-metrics \
  oci://ghcr.io/prometheus-community/charts/kube-state-metrics \
  --namespace monitoring -f values.yml
```

## Key Configuration

| Setting | Value |
|---|---|
| Metrics | ServiceMonitor enabled (scraped by VictoriaMetrics) |
| CPU | 10–100m |
| Memory | 32–100Mi |

## Resources

- [kube-state-metrics Documentation](https://github.com/kubernetes/kube-state-metrics)
- [Helm Chart (prometheus-community)](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-state-metrics)
