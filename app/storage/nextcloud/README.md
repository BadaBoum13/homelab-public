helm repo add nextcloud https://nextcloud.github.io/helm/
helm repo update

helm upgrade --install nextcloud nextcloud/nextcloud -n nextcloud --values values.yml



values url: https://github.com/nextcloud/helm/blob/main/charts/nextcloud/values.yaml


https://host/login?direct=1