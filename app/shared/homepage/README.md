# Homepage

[Homepage](https://gethomepage.dev) is a self-hosted application dashboard. In
this homelab it runs with a cluster-wide service account and auto-discovers
ingresses labelled `gethomepage.dev/enabled: "true"`, giving a single landing
page for every app exposed through traefik.

## Resources

- [Homepage Documentation](https://gethomepage.dev/installation/k8s/)
- [Helm Chart values reference](https://github.com/jameswynn/helm-charts/blob/homepage-2.1.0/charts/homepage/values.yaml)
