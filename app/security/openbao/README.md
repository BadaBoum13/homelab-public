helm repo add openbao https://openbao.github.io/openbao-helm
helm install openbao openbao/openbao


https://github.com/openbao/openbao-helm/blob/main/charts/openbao/values.yaml

#####
apt install softhsm2 opensc

# Init token SoftHSM2
softhsm2-util --init-token --free \
  --label "openbao-token" \
  --pin "ton-pin-user" \
  --so-pin "ton-pin-so"

# Créer la clé AES-256
pkcs11-tool \
  --module /usr/lib/x86_64-linux-gnu/softhsm/libsofthsm2.so \
  --token-label "openbao-token" \
  --login --pin "ton-pin-user" \
  --keygen --key-type aes:32 \
  --label "openbao-unseal-key" --id 01

# Créer le secret Kubernetes avec le PIN
kubectl create secret generic openbao-hsm-pin \
  --from-literal=pin="ton-pin-user" \
  -n openbao

# export the key in dashlane
softhsm2-util --export-token