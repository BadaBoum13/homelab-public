Dependency:
    helm install prometheus-operator-crds oci://ghcr.io/prometheus-community/charts/prometheus-operator-crds --namespace monitoring --create-namespace


helm repo add vm https://victoriametrics.github.io/helm-charts/

helm install victoriametrics-operator-crds vm/victoria-metrics-operator-crds -n monitoring --create-namespace
helm install victoriametrics-operator vm/victoria-metrics-operator -f values.yaml -n monitoring

