# Kubernetes / Helm (Phase 6)

In-repo K8s deliverable for Payment Copilot, per `prd.md` §11's Phase 6
scope ("K8s manifests/Helm chart in-repo"). The **live demo runs on Cloud
Run** (see the repo root `README.md`'s Deployment section) — this chart
is a portfolio artifact demonstrating the same container is
Kubernetes-deployable, validated locally rather than deployed to a live
cluster (no ongoing GKE cost).

Chart: [`paymentcopilot/`](paymentcopilot/). Same architecture as Cloud
Run — the image reads config from a ConfigMap and points at external
managed Postgres/Redis (Neon/Upstash-shaped connection strings) via a
Secret, rather than bundling Postgres/Redis subcharts.

## Local validation

```
helm lint deploy/helm/paymentcopilot
helm template payment-copilot deploy/helm/paymentcopilot \
  --set secret.values.ANTHROPIC_API_KEY=dummy \
  --set secret.values.PINECONE_API_KEY=dummy \
  --set secret.values.DATABASE_URL=postgresql://dummy \
  --set secret.values.REDIS_URL=rediss://dummy \
  | kubectl apply --dry-run=client -f -
```

The `--dry-run=client` step is schema/API validation only (client-side,
no live cluster required).

## Deploying for real (not done as part of Phase 6)

1. Build/push the same image the CI/CD pipeline builds for Cloud Run to
   any registry the cluster can reach.
2. Either set `secret.values.*` directly (fine for a throwaway/dev
   cluster only — plaintext ends up in Helm release history) or create
   the Secret out-of-band and set `secret.existingSecretName`.
3. `helm install payment-copilot deploy/helm/paymentcopilot -f my-values.yaml`
