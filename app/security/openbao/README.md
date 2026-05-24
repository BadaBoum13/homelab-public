# openbao

OpenBao is a Vault-compatible, community-driven secrets management platform. In this homelab it serves as the central secrets store, sealed by a hardware security module (SoftHSM2 PKCS11) so the unseal key never exists in plaintext on disk. All other secret management components (External Secrets Operator, vault-config-operator) depend on it.

## Role in the Stack

OpenBao is the root of the secret management chain. It stores all sensitive values and exposes them to workloads through External Secrets Operator, which converts OpenBao secrets into native Kubernetes `Secret` objects.

```
SoftHSM2 (PKCS11 seal key)
    └──► OpenBao (openbao.home.lab)
              ├──► vault-config-operator ──► auth engines, policies, roles
              └──► External Secrets Operator ──► Kubernetes Secrets ──► workloads
```

## Architecture

- **Single instance** (HA disabled) with file storage on Longhorn
- **Auto-unseal**: SoftHSM2 PKCS11 seal — OpenBao reads the PIN from the `openbao-hsm-pin` Kubernetes secret; an RSA-4096 keypair lives in the SoftHSM2 token on the host and wraps the master key via `CKM_RSA_PKCS_OAEP` (SHA-256)
- **Image**: `ghcr.io/badaboum13/openbao-hsm` (CGO-enabled for PKCS11)
- **TLS**: disabled at the pod level — Traefik handles TLS termination at the ingress
- **Metrics**: Prometheus endpoint exposed unauthenticated on port 8200

## Deployment

**Namespace**: `openbao`  
**Sync wave**: 1

### Prerequisites: SoftHSM2 bootstrap (run once on the node)

```bash
# Install dependencies on the Kubernetes node
apt install softhsm2 opensc

# Initialize the SoftHSM2 token
softhsm2-util --init-token --free \
  --label "openbao-token" \
  --pin "<user-pin>" \
  --so-pin "<so-pin>"

# Generate the RSA-4096 unseal keypair
# (OpenBao creates the HMAC key, "openbao-hmac-key", automatically on first unseal)
pkcs11-tool \
  --module /usr/lib/x86_64-linux-gnu/softhsm/libsofthsm2.so \
  --token-label "openbao-token" \
  --login --pin "<user-pin>" \
  --keypairgen --key-type rsa:4096 \
  --label "openbao-unseal-key" --id 01

# Export and back up the token (store in Dashlane or similar)
softhsm2-util --export-token
```

### Create the Kubernetes PIN secret

```bash
kubectl create secret generic openbao-hsm-pin \
  --from-literal=pin="<user-pin>" \
  -n openbao
```

### Install via Helm

```bash
helm repo add openbao https://openbao.github.io/openbao-helm
helm upgrade --install openbao openbao/openbao \
  --namespace openbao -f values.yml
```

## Key Configuration

| Setting | Value |
|---|---|
| Version | `2.x.x` (pinned in argocd-helm.yaml) |
| Image | `ghcr.io/badaboum13/openbao-hsm` |
| Seal type | PKCS11 (SoftHSM2, `CKM_RSA_PKCS_OAEP`, RSA-4096, SHA-256) |
| HSM PIN source | Secret `openbao-hsm-pin` / key `pin` |
| Storage | File storage, 1Gi PVC on `longhorn` |
| Ingress | `openbao.biduleproofzone.ovh` via Traefik, TLS via cert-manager (`cloudflare` issuer) |
| UI | Enabled |
| HA | Disabled |
| Server CPU | 100–500m |
| Server memory | 128–256Mi |
| Injector CPU | 50–250m |
| Injector memory | 64–128Mi |
| Prometheus monitoring | Enabled (unauthenticated) |
| Scrape interval | 30s |

## Resources

- [OpenBao Documentation](https://openbao.org/docs/)
- [OpenBao Documentation pkcs11](https://openbao.org/docs/configuration/seal/pkcs11/)
- [openbao-helm Chart values reference](https://github.com/openbao/openbao-helm/blob/main/charts/openbao/values.yaml)
- [SoftHSM2 Documentation](https://github.com/opendnssec/SoftHSMv2)
- [Grafana Dashboard](https://grafana.com/grafana/dashboards/23725-openbao)
