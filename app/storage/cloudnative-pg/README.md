# CloudNativePG

CloudNativePG is a Kubernetes operator that manages PostgreSQL clusters through
a `Cluster` custom resource. In this homelab it provides the database for apps
that need PostgreSQL (currently Immich, see `app/storage/immich/crd/database.yaml`).

## Resources

- [CloudNativePG Documentation](https://cloudnative-pg.io/documentation/current/)
- [Helm Chart values reference](https://github.com/cloudnative-pg/charts/blob/cloudnative-pg-v0.29.1/charts/cloudnative-pg/values.yaml)
