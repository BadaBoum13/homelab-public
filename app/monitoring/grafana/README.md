<<<<<<< HEAD
# Grafana Operator

Deploying Grafana using the Grafana Operator helm chart.

Grafana is an open-source analytics and visualization platform. In this homelab it provides dashboards for the entire observability stack — Kubernetes cluster health, node metrics, VictoriaMetrics performance, and log exploration.

## Role in the Stack

Grafana is the single pane of glass for observability. It reads from VictoriaMetrics as its primary data source (Prometheus-compatible API) and from VictoriaLogs for log queries.

```
VictoriaMetrics (metrics) ──┐
VictoriaLogs (logs)        ──┼──► Grafana ──► dashboards
```

## Deployment

**Namespace**: `monitoring`  
**Sync wave**: 2

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm upgrade --install grafana-operator grafana/grafana-operator -f values.yaml -n monitoring
```

## Values Reference

See the official helm chart values: https://github.com/grafana/helm-charts/blob/main/charts/grafana-operator/values.yaml

## Dashboards

See grafana-operator documentation for managing dashboards:
- https://grafana.com/docs/grafana-cloud/developer-resources/infrastructure-as-code/grafana-operator/operator-dashboards-folders-datasources/
- https://grafana.com/grafana/dashboards/17869-victoriametrics-operator/
- https://grafana.com/grafana/dashboards/14950-victoriametrics-vmalert/
- https://grafana.com/grafana/dashboards/12683-victoriametrics-vmagent/
- https://grafana.com/grafana/dashboards/16450-kubernetes-views-k3s-cluster/
- https://grafana.com/grafana/dashboards/15282-k8s-rke-cluster-monitoring/


## Access

- **URL**: `https://grafana.biduleproofzone.ovh`
- **Credentials**: managed via Kubernetes secret in the `monitoring` namespace

## Resources

- [Grafana Documentation](https://grafana.com/docs/)
- [Helm Chart values reference](https://github.com/grafana/helm-charts/blob/main/charts/grafana/values.yaml)
