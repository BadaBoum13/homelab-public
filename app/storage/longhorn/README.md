Add the Longhorn Helm repository:
    helm repo add longhorn https://charts.longhorn.io

helm upgrade --install longhorn longhorn/longhorn --namespace longhorn-system --create-namespace --version 1.9.1 --values values.yml


Linux package needed on the host: bash, curl, findmnt, grep, awk, blkid, lsblk, open-iscsi, nfs-common

values: https://github.com/longhorn/charts/blob/v1.9.x/charts/longhorn/values.yaml