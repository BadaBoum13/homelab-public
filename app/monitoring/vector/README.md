# Vector

Vector is an open-source observability data pipeline that collects logs from Kubernetes and hosts, and sends them to VictoriaMetrics for log aggregation and analysis.

## Overview

This deployment uses Vector as a DaemonSet to:
- Collect logs from all Kubernetes pods
- Gather system logs from host nodes
- Enrich logs with cluster metadata
- Stream logs to VictoriaMetrics for centralized log management

## Configuration

Vector is deployed via Flux CD using a Helm chart. The configuration includes:

### Sources
- **kubernetes_logs**: Collects logs from all pods in the cluster
- **host_logs**: Collects system logs from `/var/log/messages` and `/var/log/syslog`

### Transforms
- Metadata enrichment: Adds cluster name and environment information to all logs

### Sinks
- **VictoriaMetrics**: Sends all logs to `vmsingle-vm-single.monitoring.svc.cluster.local:6000`

## Files

- `fluxcd.yaml` - Flux CD HelmRelease and HelmRepository definitions
- `kustomization.yaml` - Kustomize configuration for the deployment
- `values.yaml` - Helm values for Vector configuration

## Deployment

Vector is automatically deployed by Flux CD. To manually apply:

```bash
kubectl apply -k app/monitoring/vector/
```

## Accessing Logs

Logs collected by Vector are available in VictoriaMetrics. You can query them through:
- Grafana dashboards connected to VictoriaMetrics
- Direct VictoriaMetrics API queries

## Resources

- [Vector Documentation](https://vector.dev/docs/)
- [Vector Helm Chart](https://helm.vector.dev/)
- [VictoriaMetrics Integration](https://vector.dev/docs/reference/sinks/vector/)
