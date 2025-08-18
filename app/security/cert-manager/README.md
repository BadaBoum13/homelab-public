kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.18.2/cert-manager.crds.yaml

helm upgrade --install cert-manager oci://quay.io/jetstack/charts/cert-manager --version v1.18.2 --namespace security -f values.yml