[fluxcd documentation](https://fluxcd.io/flux/get-started/)

[operator documentation](https://fluxcd.control-plane.io/operator/)
## installation

curl -s https://fluxcd.io/install.sh | sudo bash

## deploy

flux bootstrap gitlab --owner=BadaBoum13 --repository=homelab-public  --branch=main --token-auth --personal


helm install: https://fluxcd.io/flux/installation/#bootstrap-with-flux-operator


GitHub Container Registry (GHCR) requires authentication for OCI pulls via Helm, even when the chart is public
```
helm registry login ghcr.io \
  --username "XXXXXXX" \
  --password "XXXXXXXX"

helm install flux-operator oci://ghcr.io/controlplaneio-fluxcd/charts/flux-operator \
  --namespace flux-system \
  --create-namespace
```