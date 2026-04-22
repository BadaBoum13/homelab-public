CRD: kubectl apply -k https://github.com/argoproj/argo-cd/manifests/crds\?ref\=stable

helm repo add argo https://argoproj.github.io/argo-helm
helm install my-release argo/argo-cd

https://github.com/argoproj/argo-helm/blob/main/charts/argo-cd/values.yaml

TODO:
- add sso
- add repo