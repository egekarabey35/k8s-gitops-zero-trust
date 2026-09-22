# Kubernetes GitOps & Zero-Trust Infrastructure

Production-grade Kubernetes architecture enforcing strict Zero-Trust Network Policies, Pod Security Standards (Restricted PSS), and continuous reconciliation via ArgoCD (GitOps).

## Architecture & Security Highlights

- **Pod Security Standards (Restricted):** Rejects privileged containers, root execution, and privilege escalation at namespace level.
- **Zero-Trust Network Microsegmentation:** Default-Deny Ingress and Egress. Explicit whitelist allows only frontend pods to reach redis-backend on port 6379.
- **GitOps Continuous Delivery:** Declarative sync managed by ArgoCD with automated self-healing.
- **Automated Security Gate:** GitHub Actions pipeline running kube-linter to block insecure manifests before deployment.

## Verification Commands

Pod Security rejection test:
```bash
kubectl run privileged-test --image=busybox --restart=Never -n production --command -- sleep 60
```

Traffic whitelist test:
```bash
FRONTEND_POD=$(kubectl get pod -l app=frontend -n production -o jsonpath="{.items[0].metadata.name}")
kubectl exec -n production $FRONTEND_POD -- nc -zvw3 redis-backend 6379
```
