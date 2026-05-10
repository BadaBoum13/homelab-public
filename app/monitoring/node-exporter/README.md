# node-exporter

Prometheus Node Exporter collects hardware and operating system metrics from the host — CPU usage, memory, disk I/O, network throughput, filesystem usage, etc. It runs as a DaemonSet so every node in the cluster is covered.

## Role in the Stack

node-exporter provides the host-level layer of the observability stack, complementing kube-state-metrics (Kubernetes object state) and application-level metrics.

```
Host OS / hardware ──► node-exporter (DaemonSet) ──► VMAgent ──► VMSingle ──► Grafana
```

## Deployment

**Namespace**: `monitoring`  
**Kind**: DaemonSet  
**Sync wave**: 2

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install node-exporter prometheus-community/prometheus-node-exporter \
  -f values.yml -n monitoring
```

## Key Configuration

| Setting | Value |
|---|---|
| Metrics | ServiceMonitor enabled (scraped by VictoriaMetrics) |
| CPU | 10–100m |
| Memory | 100Mi |

## Resources

- [node-exporter Documentation](https://github.com/prometheus/node_exporter)
- [Helm Chart values reference](https://github.com/prometheus-community/helm-charts/blob/main/charts/prometheus-node-exporter/values.yaml)
