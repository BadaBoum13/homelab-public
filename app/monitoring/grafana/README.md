# Grafana Operator

Deploying Grafana using the Grafana Operator helm chart.

## Installation

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