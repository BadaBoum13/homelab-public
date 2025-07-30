# argocd

## installation

### install argocd in the cluster

``` sh
helm repo add argo https://argoproj.github.io/argo-helm
helm install --create-namespace --namespace argocd -f helm/argocd_installation_values.yaml argocd argo/argo-cd
```

Access UI: `kubectl port-forward service/argocd-server -n argocd 8080:443`
Get admin password: `kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d`
    username: admin

### install argocd cli

```
curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd
rm argocd-linux-amd64
```