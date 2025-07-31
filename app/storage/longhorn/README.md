Add the Longhorn Helm repository:
    helm repo add longhorn https://charts.longhorn.io

helm install longhorn longhorn/longhorn --namespace longhorn-system --create-namespace --version 1.9.1 --values /home/julien/workspace/homelab-public/app/storage/longhorn/values.yml


Linux package needed on the host: bash, curl, findmnt, grep, awk, blkid, lsblk, open-iscsi, nfs-common
