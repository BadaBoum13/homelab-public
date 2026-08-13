# PostgreSQL

PostgreSQL is a shared relational database instance used by applications in the cluster that require SQL storage. Currently it serves as the backend database for Nextcloud.

## Role in the Stack

```
Nextcloud ──► PostgreSQL (shared namespace) ──► Longhorn SSD (8Gi)
```

The instance is shared across applications to reduce overhead on a single-node cluster, rather than running a dedicated database per application.

## Deployment

**Namespace**: `shared`  
**Sync wave**: 2

```bash
helm install postgresql -n shared -f values.yml \
  oci://registry-1.docker.io/bitnamicharts/postgresql
```

## Key Configuration

| Setting | Value |
|---|---|
| Default database | `nextcloud` |
| Default user | `nextcloud` |
| Port | 5432 |
| Persistence | 8Gi on `longhorn-ssd` |
| CPU | 250–500m |
| Memory | 256–512Mi |
| Credentials | Externally managed Kubernetes secret |

## Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Bitnami PostgreSQL Helm Chart](https://github.com/bitnami/charts/tree/main/bitnami/postgresql)
