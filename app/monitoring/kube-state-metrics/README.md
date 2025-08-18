helm upgrade --install kube-state-metrics oci://ghcr.io/prometheus-community/charts/kube-state-metrics \
  --namespace monitoring -f values.yml
