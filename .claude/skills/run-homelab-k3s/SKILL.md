---
name: run-homelab-k3s
description: Run, inspect, validate, and smoke-test the homelab k3s cluster and its ArgoCD apps. Use when asked to run/start/deploy/screenshot/check the homelab, render or lint a Helm app, diff an app against the live cluster, check cluster or ArgoCD health, probe the ingress endpoints, tail pod logs, or syntax-check the Ansible playbooks.
---

# run-homelab-k3s

This repo is not an app you launch — it is a **single-node k3s cluster reconciled
by ArgoCD from git**. "Running it" means one of two things, and the driver does
both:

- **offline** — parse every ArgoCD `Application` under `app/`, reproduce locally
  exactly what ArgoCD would render (`helm template` / raw manifests), and
  validate it. No cluster needed. **This is the layer nearly every commit here
  touches** (chart versions, values, resource limits).
- **live** — read-only inspection of the running cluster, server-side dry-run
  diffs, and real HTTP probes through Traefik.

Driver: **`.claude/skills/run-homelab-k3s/driver.py`**. All paths below are
relative to the repo root. Run it from the repo root.

The driver never mutates the cluster. There is deliberately **no `apply`
subcommand** — prod is reconciled by ArgoCD from git, not from a laptop.

## Prerequisites

Everything was already present on this machine; no installs were needed. Required:

```bash
kubectl version --client   # v1.29.2
helm version --short       # v3.20.0+gb2e4314
/usr/bin/python3 -c 'import yaml; print(yaml.__version__)'   # 6.0.2
```

The driver uses `/usr/bin/python3` + PyYAML. **Do not use `yq`** here — the snap
build fails intermittently in WSL (`cannot preserve mount namespace ... Invalid
argument`), which is why the driver parses YAML in Python instead.

Cluster access (live commands only):

```bash
export KUBECONFIG=~/.kube/config-k3s-prod   # the driver defaults to this path
kubectl get nodes                            # controlplane1  Ready  v1.36.3+k3s1
```

The node is **LAN-only** (`192.168.1.100`). Off the LAN every live command fails
with `no route to host`; the offline half still works.

## Run (agent path)

Start here. One command, safe to run unattended:

```bash
.claude/skills/run-homelab-k3s/driver.py smoke            # waves + lint + status + ingress
.claude/skills/run-homelab-k3s/driver.py smoke --offline  # skip the cluster
```

Exit status is 1 when anything fails, so it works as a check. **It currently
exits 1 on a clean checkout** — see [Known-broken apps](#known-broken-apps).

### Offline — no cluster required

```bash
# what ArgoCD applies, in the order it applies it
.claude/skills/run-homelab-k3s/driver.py waves

# render one app exactly as ArgoCD would (pulls the real chart)
.claude/skills/run-homelab-k3s/driver.py render grafana

# render everything into /tmp/homelab-render/<app>.yaml
.claude/skills/run-homelab-k3s/driver.py render --all

# render + structurally validate every object (pure python, no kubectl)
.claude/skills/run-homelab-k3s/driver.py lint
```

`<app>` accepts an Application name (`grafana`), a directory
(`app/monitoring/grafana`), or a unique substring.

### Live — read-only

```bash
# node, ArgoCD app sync/health, unhealthy pods, ingress, certs + expiry, PVCs
.claude/skills/run-homelab-k3s/driver.py status

# real schema + admission validation against the live API (server dry-run, no writes)
.claude/skills/run-homelab-k3s/driver.py lint --cluster

# does git match the cluster? server-side dry-run diff
.claude/skills/run-homelab-k3s/driver.py diff traefik-config
.claude/skills/run-homelab-k3s/driver.py diff grafana --quiet     # counts only
.claude/skills/run-homelab-k3s/driver.py diff --all --quiet

# HTTP through Traefik: status code + TLS verification per ingress host
.claude/skills/run-homelab-k3s/driver.py ingress

# tail logs of pods whose name matches
.claude/skills/run-homelab-k3s/driver.py logs grafana --tail 20 --limit 1
```

Verified `ingress` output — this is the end-to-end path (DNS → Traefik → TLS → app);
`tls=0` means the certificate verified:

```
  ok   argocd.biduleproofzone.ovh     argocd           200 tls=0 time=0.023460s
  ok   longhorn.biduleproofzone.ovh   longhorn-system  200 tls=0 time=0.024495s
  ok   grafana.biduleproofzone.ovh    monitoring       302 tls=0 time=0.022649s
  FAIL openbao.biduleproofzone.ovh    security         503 tls=0 time=0.022355s
```

`ingress` resolves each host to the node IP with `curl --resolve`, so it works
without trusting public DNS. Override with `--node-ip`.

### Ansible

```bash
.claude/skills/run-homelab-k3s/driver.py ansible            # syntax-check, prod inventory
.claude/skills/run-homelab-k3s/driver.py ansible --env dev
```

No host is contacted. All 5 playbooks pass.

## Run (human path)

`task dev` provisions a throwaway dev cluster (docker container + Ansible + k3s).
**It cannot run on this machine** — there is no Linux docker daemon (no
`/var/run/docker.sock`, no `dockerd`; `docker` resolves only to the Docker
Desktop wrapper under `/mnt/c`, which refuses to run). `k3d` and `minikube` are
installed but need the same runtime. Do not reach for the Windows `.exe`.

Deploying for real is a git push — ArgoCD self-heals and prunes.

## Gotchas

- **`diff` always shows drift on `argocd.argoproj.io/tracking-id`.** ArgoCD adds
  that annotation to every object it manages; the git manifest has no such
  annotation, so every diff opens with it. Ignore it. `generation` bumps are the
  same kind of noise.
- **`diff grafana` never comes back clean.** The chart generates a *random* admin
  password on every `helm template`, so the `Secret` and the Deployment's
  `checksum/secret` annotation differ on every run. Verified: two consecutive
  renders produce different `admin-password` values. Phantom drift, not real.
- **Helm `test` hooks break `kubectl diff`.** `grafana-test` is a Pod referencing
  a ServiceAccount that does not exist, and it makes `kubectl diff` bail with
  `Forbidden ... serviceaccount "grafana-test" not found` *before* it reaches
  the real objects. The driver strips `helm.sh/hook: test` resources
  (`strip_test_hooks`). If you render with plain `helm template`, you will hit this.
- **OCI charts need a different helm invocation.** `oci://` sources must be
  addressed as one ref (`helm template x oci://host/ns/chart --version v`);
  passing `--repo oci://...` fails with `not a valid chart repository`. The
  driver handles it — but note **every OCI-sourced app is currently failing in
  ArgoCD** (see below), so the driver is stricter than the live reconciler here.
- **`valueFiles` without a `$values/` prefix silently ignores the repo.** Only
  `$values/<path>` resolves against this repo (via the `ref: values` source). A
  bare `values.yaml` resolves against the *chart*, so a repo-local file of the
  same name is never read. `openbao` is in exactly that state; the driver warns.
- **An `include:` pattern that matches nothing yields `Synced`/`Healthy`.** An
  ArgoCD app that renders zero objects is trivially healthy, so the dashboard
  looks green while the app manages nothing. Confirm with
  `kubectl get application <name> -n argocd -o jsonpath='{.status.resources}'` —
  empty means it manages nothing. `include:` globs against file paths, not
  directory names — `include: "crd"` never matches anything inside a `crd/`
  folder; use `include: "crd/*"`. `cert-manager-config` and `longhorn-config`
  were in this state and are now fixed; `vault-config-operator-config` was in
  this state and has been removed (its `crd/` folder never existed — that
  app's config is applied via Ansible, not VCO CRDs). The driver reports
  apps in this state as `EMPTY`, not `ok`.
- **`ansible-playbook` on PATH is broken.** `~/.local/bin/ansible-playbook` has a
  `#!/usr/bin/python3` shebang and that interpreter has no `ansible` module
  (`ModuleNotFoundError: No module named 'ansible'`). The working binary is
  `~/.venv/ansible/bin/ansible-playbook` (core 2.17.13); the driver prefers it.
- **The README's sync-wave table is stale.** It documents waves 0–3; there is a
  wave 4 (`grafana-config`) and `openbao` carries no wave annotation at all. Use
  `driver.py waves` as the source of truth.
- **The vault's secret-management ADRs contradict the cluster.** ADR-0002 /
  ADR-0003 / `project map` (May 2026) describe External Secrets Operator as the
  path forward and vault-config-operator as removed. The live cluster is the
  reverse: `vault-config-operator` is installed (redhatcop.redhat.io CRDs) and
  `external-secrets-operator` sits in `app/deprecated/` with **no** ESO CRDs
  installed. Trust the cluster, and treat those notes as out of date.

## Known-broken apps

Found by the driver and confirmed against live ArgoCD state. `smoke` exits 1
because of these — it is not a driver bug.

| App | Problem |
|---|---|
| `longhorn` | `argocd-helm.yaml:16` points at `$values/app/storage/longhorn/values.yml`, but the file is `values.**yaml**`. ArgoCD: `open .../values.yml: no such file or directory`, sync `Unknown`. |
| `prometheus-operator-crds` | Pinned to `76.2.0`, which does not exist for that chart (latest is `31.0.1`; `76.2.0` is the `kube-prometheus-stack` version). Sync `Unknown`. |
| `cert-manager`, `kube-state-metrics` | OCI charts. ArgoCD resolves the digest without appending the chart name (`quay.io/v2/jetstack/charts/manifests/v1.21.1`) → 401/403, sync `Unknown`. Both render fine locally. |
| `openbao` | Sync fails on an invalid StatefulSet: `readinessProbe.httpGet: Forbidden: may not specify more than 1 handler type`, plus immutable-field updates. Pod sealed → ingress returns 503. `lint --cluster` reproduces this exactly. |

## Troubleshooting

| Symptom | Fix |
|---|---|
| `couldn't get current server API group list: ... localhost:8080` | A live command ran without `KUBECONFIG`. Driver defaults to `~/.kube/config-k3s-prod`; export it or pass it. |
| `dial tcp 192.168.1.100:6443: connect: no route to host` | Off the LAN / node down. Use the offline commands (`waves`, `render`, `lint`, `ansible`). |
| `yq: cannot preserve mount namespace ... Invalid argument` | Snap `yq` is flaky in WSL. Don't use it; the driver uses `/usr/bin/python3` + PyYAML. |
| `not a valid chart repository or cannot be reached: ... invalid reference` | An `oci://` chart invoked with `--repo`. Use one combined ref (the driver does). |
| `helm template` hangs or is slow on `render --all` | It pulls every chart from the network each run; a cold run takes minutes. Rendered output is cached in `/tmp/homelab-render/`. |
| `kubectl diff` exits non-zero with `Forbidden ... grafana-test` | A test hook leaked into the manifest. Render through the driver, not bare `helm template`. |

## Where output lands

`/tmp/homelab-render/<app>.yaml` — every rendered app. Override with `DRIVER_OUT`.
