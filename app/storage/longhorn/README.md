# Longhorn

Longhorn is a cloud-native distributed block storage system for Kubernetes. In this homelab it provides persistent volume storage backed by two physical storage tiers: an SSD for fast workloads and an HDD RAID array for bulk data.

## TODO

add disk tag with crd

## Role in the Stack

Longhorn is the storage layer for every stateful workload in the cluster. It provisions `PersistentVolumes` on demand and exposes multiple storage classes tuned to different performance and durability requirements.

```
SSD (/mnt/short_live_storage) ──► longhorn-ssd           ← databases, metrics, fast I/O
HDD RAID (/mnt/long_storage)  ──► longhorn-raid           ← Nextcloud bulk data
SSD (temp)                    ──► longhorn-ssd-short-live ← ephemeral / test workloads
```

## Deployment

**Namespace**: `longhorn-system`  
**Sync wave**: 1

**Host requirements** (installed via Ansible bootstrap playbook):
- `open-iscsi`, `nfs-common`, `bash`, `curl`, `findmnt`, `grep`, `awk`, `blkid`, `lsblk`

```bash
helm repo add longhorn https://charts.longhorn.io
helm upgrade --install longhorn longhorn/longhorn \
  --namespace longhorn-system --create-namespace \
  --version 1.9.1 --values values.yml
```

## Key Configuration

| Setting | Value |
|---|---|
| Version | 1.9.1 |
| URL | `https://longhorn.biduleproofzone.ovh` |
| Default replica count | 1 (single-node cluster) |
| HDD data path | `/mnt/long_storage` |
| SSD data path | `/mnt/short_live_storage` |
| Node selector (driver) | `storage-raid=true` |
| Metrics | ServiceMonitor enabled |
| Ingress | Traefik + cert-manager (CloudFlare issuer) |

### Storage Classes

| Class | Binding | Use case |
|---|---|---|
| `longhorn-ssd` | WaitForFirstConsumer | Fast persistent storage (databases, metrics) |
| `longhorn-raid` | Immediate | Bulk storage (Nextcloud data) |
| `longhorn-ssd-short-live` | WaitForFirstConsumer | Temporary or disposable data |

## Access

- **URL**: `https://longhorn.biduleproofzone.ovh`

## Resources

- [Longhorn Documentation](https://longhorn.io/docs/)
- [Helm Chart values reference](https://github.com/longhorn/charts/blob/v1.9.x/charts/longhorn/values.yaml)
