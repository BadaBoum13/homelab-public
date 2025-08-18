helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install node-exporter prometheus-community/prometheus-node-exporter -f values.yml


values: https://github.com/prometheus-community/helm-charts/blob/main/charts/prometheus-node-exporter/values.yaml