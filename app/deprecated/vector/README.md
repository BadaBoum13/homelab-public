# Vector

Vector is a high-performance observability data pipeline. In this homelab it runs as a DaemonSet on every node to collect logs from all Kubernetes pods and system services, enrich them with cluster metadata, and ship them to VictoriaLogs.

## Role in the Stack

Vector is the log collection layer of the observability stack:

```
Kubernetes pod logs ──┐
Host system logs    ──┼──► Vector (DaemonSet) ──► VictoriaLogs
                      │         (enrich with
                      │          cluster metadata)
```

Data flows:
- **Sources**: `kubernetes_logs` (all pod stdout/stderr) + `host_logs` (`/var/log/messages`, `/var/log/syslog`)
- **Transforms**: metadata enrichment — adds `cluster_name=homelab` and `env=prod` to every log event
- **Sink**: HTTP to VictoriaLogs at `vlsingle-vl-single.monitoring.svc.cluster.local:9428` with gzip compression

## Deployment

**Namespace**: `monitoring`  
**Kind**: DaemonSet (runs on all nodes, including nodes with NoSchedule/NoExecute taints)  
**Sync wave**: 2

Vector is deployed via ArgoCD using the official Helm chart.

## Key Configuration

| Setting | Value |
|---|---|
| Role | Agent (DaemonSet) |
| Log sources | Kubernetes pods + host system logs |
| Destination | VictoriaLogs HTTP endpoint (gzip) |
| Batch size | 200 events or 5s timeout |
| Buffer persistence | 100Mi |
| Cluster name | `homelab` |
| Environment | `prod` |
| Tolerations | NoSchedule + NoExecute (all nodes) |

## Files

- `values.yaml` — Helm values with full pipeline configuration
- `argocd-helm.yaml` — ArgoCD Application manifest

## Accessing Logs

Logs collected by Vector are available in VictoriaLogs and can be queried through:
- Grafana dashboards connected to VictoriaLogs
- Direct VictoriaLogs API queries at `vlsingle-vl-single.monitoring.svc.cluster.local:9428`

## Resources

- [Vector Documentation](https://vector.dev/docs/)
- [Vector Helm Chart](https://helm.vector.dev/)
- [VictoriaLogs HTTP sink](https://docs.victoriametrics.com/victorialogs/data-ingestion/)
