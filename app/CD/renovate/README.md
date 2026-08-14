# Renovate

Renovate is a self-hosted dependency-update bot. It runs as a weekly CronJob that scans this repository and opens pull requests bumping outdated versions — Helm chart pins in ArgoCD `Application` manifests (`app/**/argocd-helm.yaml`), and the `xanmanning.k3s` Ansible role/collection versions in `system/ansible/requirements.yml`.

## Role in the Stack

Renovate closes the loop on this repo's GitOps model: it detects new upstream versions, opens a PR against `BadaBoum13/homelab-public`, and once merged, ArgoCD's `automated.selfHeal` picks up the change and syncs it — the same way every other version bump (e.g. Longhorn, cert-manager) is applied today, just automated instead of manual.

`k3s_release_version` in the Ansible inventories is intentionally **not** scanned — it's a channel selector (e.g. `v1.36`) resolved dynamically by the `xanmanning.k3s` role, not a pinned release tag, so auto-bumping it could silently change upgrade semantics. k3s minor-version bumps stay a deliberate manual change.

## Deployment

**Namespace**: `renovate`
**Sync wave**: 2 (Helm release), 4 (config: `VaultSecret` + `renovate.json` ConfigMap)

```bash
kubectl create namespace renovate --dry-run=client -o yaml | kubectl apply -f -

helm repo add renovate https://renovatebot.github.io/helm-charts
helm upgrade --install renovate renovate/renovate \
  --version 46.251.0 --namespace renovate -f values.yaml

kubectl apply -f crd
```

## Key Configuration

| Setting | Value |
|---|---|
| Chart version | 46.251.0 (Renovate 43.288.0) |
| Schedule | Monday 03:00 (`0 3 * * 1`) |
| Managers enabled | `argocd`, `ansible-galaxy` |
| Scope | `BadaBoum13/homelab-public` only (`autodiscover: false`) |
| Excluded paths | `app/deprecated/**` |
| CPU | 100–500m |
| Memory | 256Mi–1Gi |

## GitHub token

Renovate needs a GitHub token with `contents:write` + `pull-requests:write` + `issue:write` on `BadaBoum13/homelab-public` (a fine-grained PAT scoped to just this repo is recommended). It's injected via a `VaultSecret` (`crd/github-token.yml`), the same pattern used by [ArgoCD's own repo credential](../argoCD/crd/github-homelab-public.yml) and [cert-manager's CloudFlare token](../cert-manager/crd/token.yml).

**Inject the token** (one-time, not committed to git):
```bash
bao kv put secret/renovate/renovate token=ghp_...
```

## Resources

- [renovatebot/helm-charts](https://github.com/renovatebot/helm-charts)
- [Helm Chart values reference](https://github.com/renovatebot/helm-charts/blob/main/charts/renovate/values.yaml)
- [Renovate self-hosted configuration](https://docs.renovatebot.com/self-hosted-configuration/)
- [Renovate `argocd` manager](https://docs.renovatebot.com/modules/manager/argocd/)
- [Renovate `ansible-galaxy` manager](https://docs.renovatebot.com/modules/manager/ansible-galaxy/)
