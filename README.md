# homelab-public

Personal homelab running on a single-node K3s cluster, managed as code with Ansible for infrastructure provisioning and ArgoCD for GitOps application delivery.

## Architecture

```
Internet
   │
   ▼
CloudFlare DNS (biduleproofzone.ovh)
   │  TLS via Let's Encrypt (DNS01 challenge)
   ▼
Traefik (Ingress Controller)
   │
   ├── argocd.biduleproofzone.ovh  ──► ArgoCD
   ├── grafana.biduleproofzone.ovh ──► Grafana
   ├── longhorn.biduleproofzone.ovh──► Longhorn UI
   └── nextcloud.biduleproofzone.ovh──► Nextcloud

Node (192.168.1.100) — K3s single-node cluster
   ├── /mnt/short_live_storage  (SSD — fast, small)
   └── /mnt/long_storage        (HDD RAID — bulk data)

VPN: Tailscale (exit node + SSH)
```

### Node

- Single AMD64 node provisioned via Ansible
- K3s lightweight Kubernetes distribution
- Tailscale for secure remote access and SSH

### Storage Strategy

| Class | Backend | Mount | Use |
|---|---|---|---|
| `longhorn-ssd` | SSD | `/mnt/short_live_storage` | Databases, metrics, fast I/O |
| `longhorn-raid` | HDD RAID | `/mnt/long_storage` | Nextcloud bulk data |
| `longhorn-ssd-short-live` | SSD | `/mnt/short_live_storage` | Temporary / ephemeral |

### Networking

All ingress routes through Traefik with a global HTTP→HTTPS redirect. TLS certificates are issued automatically by cert-manager using Let's Encrypt ACME with CloudFlare DNS01 validation.

---

## Stack

| Category | Tool | Purpose |
|---|---|---|
| **Kubernetes** | K3s | Lightweight single-node cluster |
| **GitOps / CD** | ArgoCD | Declarative app delivery, self-healing sync |
| **Ingress** | Traefik | Reverse proxy, HTTP→HTTPS, TLS termination |
| **TLS** | cert-manager | Automated Let's Encrypt certificates |
| **Storage** | Longhorn | Distributed block storage (SSD + RAID) |
| **Metrics** | VictoriaMetrics | Time-series metrics DB (365-day retention) |
| **Logs** | VictoriaLogs | Log storage (10-day retention) |
| **Log pipeline** | Vector | DaemonSet collecting and shipping logs |
| **Metrics exporters** | kube-state-metrics, node-exporter | K8s object + host-level metrics |
| **Visualization** | Grafana | Dashboards for metrics and logs |
| **Database** | PostgreSQL | Shared relational DB (used by Nextcloud) |
| **Cloud storage** | Nextcloud | Self-hosted file sync and collaboration |
| **Resource advisor** | KRR | Kubernetes resource request/limit recommendations |
| **Provisioning** | Ansible | Node bootstrap, K3s install, Tailscale setup |

---

## Repository Structure

```
.
├── app/                        # Kubernetes applications
│   ├── CD/
│   │   └── argoCD/             # ArgoCD — GitOps platform
│   ├── deprecated/
│   │   └── fluxcd/             # Replaced by ArgoCD
│   ├── krr/                    # KRR — resource recommender
│   ├── monitoring/
│   │   ├── grafana/            # Grafana — dashboards
│   │   ├── kube-state-metrics/ # K8s object metrics exporter
│   │   ├── node-exporter/      # Host-level metrics exporter
│   │   ├── prometheus-operator-crds/ # CRDs required by VictoriaMetrics
│   │   ├── victoriametrics/    # Metrics + logs database
│   │   └── vector/             # Log collection pipeline
│   ├── network/
│   │   └── traefik/            # Ingress controller config
│   ├── security/
│   │   └── cert-manager/       # TLS certificate automation
│   ├── shared/
│   │   └── postgresql/         # Shared PostgreSQL instance
│   └── storage/
│       ├── longhorn/           # Distributed block storage
│       └── nextcloud/          # Self-hosted cloud storage
└── system/
    └── ansible/                # Infrastructure provisioning
        ├── playbooks/          # bootstrap, install_k3s, tailscale
        ├── group_vars/
        └── host_vars/
```

---

## Deployment Order (ArgoCD Sync Waves)

ArgoCD deploys applications in waves to respect dependency ordering:

| Wave | Applications | Reason |
|---|---|---|
| 0 | prometheus-operator-crds | CRDs must exist before VictoriaMetrics operator |
| 1 | cert-manager, longhorn, victoriametrics-operator-crds | Infrastructure layer |
| 2 | postgresql, kube-state-metrics, grafana, vector, node-exporter, victoriametrics, nextcloud | Applications and monitoring stack |
| 3 | victoriametrics-config, traefik-config, cert-manager-config, longhorn-config | Configuration CRs applied after operators are ready |

---

## Getting Started

### 1. Provision the node

```bash
cd system/ansible
ansible-playbook -i inventory.yml playbooks/bootstrap.yml
ansible-playbook -i inventory.yml playbooks/tailscale.yml
ansible-playbook -i inventory.yml playbooks/install_k3s.yml
```

### 2. Bootstrap ArgoCD

```bash
kubectl apply -k app/CD/argoCD/
```

### 3. Apply the bootstrap application

```bash
kubectl apply -f app/argocd-bootstrap.yaml
```

ArgoCD will then reconcile all other applications automatically.

---

## Applications

- [ArgoCD](app/CD/argoCD/README.md) — GitOps continuous delivery
- [Traefik](app/network/traefik/README.md) — Ingress controller
- [cert-manager](app/security/cert-manager/README.md) — TLS automation
- [Longhorn](app/storage/longhorn/README.md) — Block storage
- [VictoriaMetrics](app/monitoring/victoriametrics/README.md) — Metrics & logs
- [Grafana](app/monitoring/grafana/README.md) — Dashboards
- [Vector](app/monitoring/vector/README.md) — Log pipeline
- [kube-state-metrics](app/monitoring/kube-state-metrics/README.md) — K8s metrics
- [node-exporter](app/monitoring/node-exporter/README.md) — Host metrics
- [PostgreSQL](app/shared/postgresql/README.md) — Shared database
- [Nextcloud](app/storage/nextcloud/README.md) — Cloud storage
- [KRR](app/krr/README.md) — Resource recommender
