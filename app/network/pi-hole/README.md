helm repo add mojo2600 https://mojo2600.github.io/pihole-kubernetes/
helm repo update

helm upgrade --install pihole mojo2600/pihole -n pihole --values values.yml

values: https://github.com/MoJo2600/pihole-kubernetes/blob/main/charts/pihole/values.yaml

whitelist: https://github.com/anudeepND/whitelist
blocklist: https://firebog.net/


common whitelist: https://discourse.pi-hole.net/t/commonly-whitelisted-domains/212

TODO:
- https://github.com/jacklul/pihole-updatelists