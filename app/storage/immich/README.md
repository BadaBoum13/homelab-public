# Immich

Immich is a self-hosted photo and video backup platform (mobile auto-upload,
face/object search via its machine-learning service). It complements ownCloud
(`app/storage/owncloud`): Immich owns the photo library, ownCloud the documents.
Login goes through the same Auth0 tenant.

| Object | File |
|---|---|
| Helm chart values | `values.yaml` |
| Library PVC (`longhorn-raid`) | `crd/library-pvc.yaml` |
| PostgreSQL (CloudNativePG `Cluster`, VectorChord) | `crd/database.yaml` |
| Immich config file with Auth0 OAuth, from OpenBao | `crd/oidc.yaml` |

## Auth0 setup

1. Create a *Regular Web Application* in Auth0 with these Allowed Callback URLs:
   `https://immich.biduleproofzone.ovh/auth/login`,
   `https://immich.biduleproofzone.ovh/user-settings`,
   `app.immich:///oauth-callback` (mobile app).
2. Store it in OpenBao at `auth0/immich/immich` with keys `issuer`
   (`https://homelab-ikyt.eu.auth0.com/`), `client_id`, `client_secret`.

The config Secret is not checksummed by the chart: after changing it, restart
the server (`kubectl -n immich rollout restart deploy immich-server`).

## Resources

- [Immich Documentation](https://docs.immich.app/)
- [Helm Chart values reference](https://github.com/immich-app/immich-charts/blob/immich-0.13.4/charts/immich/values.yaml)
