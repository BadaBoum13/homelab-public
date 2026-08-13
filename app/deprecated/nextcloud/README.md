# Nextcloud

Nextcloud is a self-hosted cloud collaboration platform providing file sync, sharing, and productivity tools. It is the primary user-facing application in this homelab, replacing commercial cloud storage with a fully private alternative.

## Role in the Stack

Nextcloud depends on several other components in the homelab:

```
Nextcloud ──► PostgreSQL (database)
         ──► Longhorn RAID 100Gi (user file storage)
         ──► Longhorn SSD 10Gi (application data)
         ──► Imaginary (image processing sidecar)
         ──► Traefik (ingress) + cert-manager (TLS)
```

## Deployment

**Namespace**: `nextcloud`  
**Sync wave**: 2

```bash
helm repo add nextcloud https://nextcloud.github.io/helm/
helm repo update
helm upgrade --install nextcloud nextcloud/nextcloud \
  -n nextcloud --values values.yml
```

## Key Configuration

| Setting | Value |
|---|---|
| URL | `https://nextcloud.biduleproofzone.ovh` |
| Database | External PostgreSQL (`shared` namespace) |
| App storage | 10Gi on `longhorn-ssd` |
| Data storage | 100Gi on `longhorn-raid` |
| Image processing | Imaginary sidecar enabled |
| CronJob | Enabled (background task runner) |
| Metrics | ServiceMonitor enabled |
| CPU | 500–2000m |
| Memory | 1024–2048Mi |
| Credentials | Externally managed Kubernetes secret |

### Preview Providers

Nextcloud is configured with preview generation for: Movie, PNG, JPEG, GIF, BMP, XBitmap, MP3, MP4, TXT, Markdown, PDF.

## Access

- **URL**: `https://nextcloud.biduleproofzone.ovh`
- **Direct login** (bypass redirect): `https://nextcloud.biduleproofzone.ovh/login?direct=1`
- **Credentials**: managed via Kubernetes secret in the `nextcloud` namespace

## Resources

- [Nextcloud Documentation](https://docs.nextcloud.com/)
- [Helm Chart values reference](https://github.com/nextcloud/helm/blob/main/charts/nextcloud/values.yaml)
