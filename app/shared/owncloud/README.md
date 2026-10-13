# ownCloud Infinite Scale (oCIS)

ownCloud Infinite Scale is a lightweight, cloud-native file sync and share
platform. It replaces Nextcloud in this homelab: Infinite Scale requires far
less manual configuration and runs with a much smaller memory footprint,
making it a better fit for a self-hosted single-node/small-cluster setup.

## Deployment

Deployed via [BadaBoum13/ocis-charts](https://github.com/BadaBoum13/ocis-charts)
(release [`v0.6.0`](https://github.com/BadaBoum13/ocis-charts/releases/tag/v0.6.0),
packaged as chart version `0.7.0` — the OCI tag is the `Chart.yaml` version,
not the git tag), a fork of `ocis-charts` that adds `secretRefs.oidcSecretRef` so
the external-OIDC mode can read the issuer/client ID from a Kubernetes
Secret instead of requiring a plaintext client ID in `values.yaml` or an
external LDAP server.

| Object | File |
|---|---|
| Helm chart values (OIDC config) | `values.yaml` |
| ArgoCD Application (chart) | `argocd-helm.yaml` |
| Auth0 issuer + client ID from OpenBao | `crd/oidc.yaml` |
| ArgoCD Application (extra manifests) | `argocd-config.yaml` |

## Auth0 integration

oCIS uses Auth0 as its OIDC provider via `features.externalUserManagement`.

### 1. Auth0 application

Single Page Application (Authorization Code + PKCE, no client secret):

| Setting | Value |
|---|---|
| Allowed Callback URLs | `https://owncloud.biduleproofzone.ovh/`, `https://owncloud.biduleproofzone.ovh/oidc-callback.html`, `https://owncloud.biduleproofzone.ovh/oidc-silent-redirect.html` |
| Allowed Logout URLs | `https://owncloud.biduleproofzone.ovh` |
| Allowed Web Origins | `https://owncloud.biduleproofzone.ovh` |

### 2. OpenBao

Secret engine `auth0`, path `auth0/owncloud/owncloud`:

| Key | Value |
|---|---|
| `issuer` | `https://<tenant>.eu.auth0.com/` (trailing slash) |
| `client_id` | the SPA application client ID |

`crd/oidc.yaml` reads it and publishes the Kubernetes secret `ocis-oidc`
(`issuer-uri`, `client-id`), referenced by `secretRefs.oidcSecretRef` in
`values.yaml`. The `vco-policy-admin` policy already grants
`auth0/data/owncloud/*` read to the `owncloud` namespace.

Set the real tenant domain in `values.yaml`
(`features.externalUserManagement.oidc.issuerURI`, replacing `<tenant>`) -
this value is not secret, it's just not committed as a real domain here.

`argocd-config.yaml` (which applies `crd/oidc.yaml`) syncs at wave 2, ahead
of the `owncloud` Helm app at wave 3, so the `ocis-oidc` secret exists
before the chart's pods start.

## Resources

- [ownCloud Infinite Scale Documentation](https://doc.owncloud.com/ocis/next/)
- [ocis-charts fork](https://github.com/BadaBoum13/ocis-charts)
