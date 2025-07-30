Add the Longhorn Helm repository:
    helm repo add longhorn https://charts.longhorn.io

helm install longhorn longhorn/longhorn --namespace longhorn-system --create-namespace --version 1.9.1