---
name: add-app
description: Scaffold a new ArgoCD-managed app under app/ — values.yaml, argocd-helm.yaml, optionally argocd-config.yaml + crd/, and a brief README.md. Use when the user wants to add, onboard, or scaffold a new app/Helm chart to the homelab cluster — e.g. "add a new app for X", "onboard <chart> to the cluster", "scaffold app/<category>/<name>".
---

# add-app

Creates the files for one new ArgoCD `Application` under `app/<category>/<app-name>/`.
No separate registration step is needed: `app/argocd-bootstrap.yaml` recursively
globs `**/{argocd-helm,argocd-helm-crds,argocd-config}.yaml` under `app/`
(excluding `deprecated/*`), so any correctly-named file dropped in the right
place is picked up automatically on the next ArgoCD sync.

Read this whole skill before writing anything — the Gotchas section below
documents two patterns that look right by analogy to existing apps but are
**currently broken** in this repo. Don't copy them.

## 1. Gather inputs

Ask the user for whatever isn't already given:

- **App name** (kebab-case, matches the chart's usual name)
- **Category**: an existing folder under `app/` (`monitoring`, `storage`,
  `security`, `network`, `CD`) or a new one — list `app/*/` and ask if unclear,
  don't guess.
- **Helm chart**: `repoURL` + `chart` name + `targetRevision` (pin an exact
  version, never a floating tag — every existing app does this)
- **Namespace**: defaults to the category name (`monitoring`, `security`, ...)
  but several apps use a dedicated one instead (`longhorn` → `longhorn-system`).
  Ask if it's not obviously the category.
- **Docs URL** and the **chart's `values.yaml` reference URL** (usually
  `https://github.com/<org>/<chart-repo>/blob/<tag>/.../values.yaml`) — needed
  for the README.
- **Does it need extra manifests** (ClusterIssuers, StorageClasses, secrets,
  CRDs not shipped by the chart)? If yes, those go in a `crd/` subfolder and
  you'll also write `argocd-config.yaml`. If no, skip that file — see
  `prometheus-operator-crds` and `kube-state-metrics`, which have no
  `argocd-config.yaml` at all.

## 2. Pick the sync-wave

Grep the existing waves to place the new app correctly:

```bash
grep -H "sync-wave" app/*/*/argocd-*.yaml | sort
```

The convention:
- `0` — CRD-only installs that everything else depends on
  (`prometheus-operator-crds`)
- `1` — foundational operators (`cert-manager`, `longhorn`, `vault-config-operator`)
- `2` — apps that depend on those operators (`grafana`, `kube-state-metrics`,
  `victoriametrics`)
- `argocd-config.yaml` (extra manifests) — **helm wave + 2** (a wave-1 app's
  config lands on wave 3, a wave-2 app's on wave 4). This gives the chart's own
  CRDs/webhooks time to become ready before dependent manifests apply.

Ask the user which tier the new app belongs in if it's not obvious from what
it depends on.

## 3. Create the files

```
app/<category>/<app-name>/
├── values.yaml
├── argocd-helm.yaml
├── argocd-config.yaml   # only if extra manifests are needed
├── crd/                 # only if extra manifests are needed
│   └── ...
└── README.md
```

### `values.yaml`

Whatever Helm values the user wants to set. If they haven't specified any yet,
start with an empty file (or the minimal keys they mention) rather than
guessing at chart defaults.

### `argocd-helm.yaml`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: <app-name>
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "<wave>"
spec:
  project: default
  sources:
    - repoURL: <chart repoURL>
      chart: <chart>
      targetRevision: "<pinned version>"
      helm:
        valueFiles:
          - $values/app/<category>/<app-name>/values.yaml
    - repoURL: https://github.com/BadaBoum13/homelab-public.git
      targetRevision: HEAD
      ref: values
  destination:
    server: https://kubernetes.default.svc
    namespace: <namespace>
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

The `$values/...` path **must exactly match the real filename**, including
extension. `longhorn` currently references `values.yml` while the file on
disk is `values.yaml` — ArgoCD fails with `open ...: no such file or
directory`. Don't repeat that typo.

### `argocd-config.yaml` (only if there's a `crd/` folder)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: <app-name>-config
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "<helm wave + 2>"
spec:
  project: default
  source:
    repoURL: https://github.com/BadaBoum13/homelab-public.git
    targetRevision: HEAD
    path: app/<category>/<app-name>
    directory:
      recurse: true
      include: "crd/*"
  destination:
    server: https://kubernetes.default.svc
    namespace: <namespace>
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

**Use `include: "crd/*"`, not `include: "crd"`.** `include`/`exclude` glob
against file paths, not directory names — `"crd"` matches nothing (a
directory name, no file is literally called `crd`), so the Application syncs
`Synced`/`Healthy` while managing **zero resources**. `cert-manager-config`
and `longhorn-config` shipped with exactly this mistake (the latter via
`include: "storageclass_*.yml"` with `recurse: false`, which never looks
inside `crd/` at all) before being fixed — don't reproduce either shape. If
the extra manifests are nested deeper than one level, use `"crd/**"` instead.

### `README.md`

Keep it brief — a short description plus links, not the longer
Deployment/Key-Configuration write-ups some existing apps have:

```markdown
# <App Name>

<One to three sentences: what the app is, and why it's in this homelab —
its role relative to what it talks to.>

## Resources

- [<App> Documentation](<docs URL>)
- [Helm Chart values reference](<chart's values.yaml URL>)
```

## 4. Verify before calling it done

No manual registration step is needed — the bootstrap glob picks up the new
files automatically. But validate the render locally with the
[run-homelab-k3s](../run-homelab-k3s/SKILL.md) skill's driver before
considering the app finished:

```bash
.claude/skills/run-homelab-k3s/driver.py render <app-name>   # renders exactly what ArgoCD would
.claude/skills/run-homelab-k3s/driver.py lint                # structural validation, no cluster needed
.claude/skills/run-homelab-k3s/driver.py waves                # confirm the new app appears in the right wave
```

## What this skill does not do

- **Taskfile.yml.** Every existing app also has a per-app `Taskfile.yml` (manual
  `helm upgrade --install` for local/offline use) registered in its category's
  `Taskfile.yml` `includes:` block. This skill doesn't create or wire one up —
  ask the user if they want it; it's optional scaffolding on top of what's
  needed for ArgoCD to manage the app.
- Choosing *whether* an app belongs in this cluster, or picking the chart
  version — that's a decision for the user, not something to infer.
