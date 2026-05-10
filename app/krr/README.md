# KRR (Kubernetes Resource Recommender)

KRR is an open-source CLI tool by Robusta that analyzes actual resource usage in a Kubernetes cluster and recommends right-sized CPU and memory `requests` and `limits` for every workload. It reads historical metrics from VictoriaMetrics (Prometheus-compatible API) to produce its recommendations.

## Role in the Stack

KRR is an on-demand analysis tool, not a continuously running service. It is deployed as a Kubernetes `Job` when you want a resource optimization report. The results help tune the `requests`/`limits` values in each application's `values.yaml`.

```
VictoriaMetrics (historical metrics) ──► KRR Job ──► recommendations report
```

## Deployment

KRR runs as a Kubernetes Job (not managed by ArgoCD — triggered manually).

```bash
# Run KRR in-cluster against VictoriaMetrics
kubectl apply -f https://raw.githubusercontent.com/robusta-dev/krr/refs/heads/main/docs/krr-in-cluster/krr-in-cluster-job.yaml
```

The Job manifest in `manifest-job.yml` is pre-configured for this cluster.

## Key Configuration

| Setting | Value |
|---|---|
| Image | `us-central1-docker.pkg.dev/genuine-flight-317411/devel/krr:v1.8.3` |
| Metrics source | VictoriaMetrics (Prometheus API) |
| Trigger | Manual Job |

## Resources

- [KRR Documentation](https://github.com/robusta-dev/krr)
- [KRR in-cluster guide](https://github.com/robusta-dev/krr/blob/main/docs/krr-in-cluster/README.md)
