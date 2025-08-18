helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm upgrade --install grafana grafana/grafana -f values.yml -n monitoring


values url: https://github.com/grafana/helm-charts/blob/main/charts/grafana/values.yaml


dashboard:
    - https://grafana.com/grafana/dashboards/17869-victoriametrics-operator/
    - https://grafana.com/grafana/dashboards/14950-victoriametrics-vmalert/
    - https://grafana.com/grafana/dashboards/12683-victoriametrics-vmagent/
    - https://grafana.com/grafana/dashboards/16450-kubernetes-views-k3s-cluster/
    - https://grafana.com/grafana/dashboards/15282-k8s-rke-cluster-monitoring/