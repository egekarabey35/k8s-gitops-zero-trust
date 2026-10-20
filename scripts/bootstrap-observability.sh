#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="monitoring"
RELEASE_NAME="kube-prometheus-stack"
VALUES_FILE="monitoring/kube-prometheus-values.yaml"

echo "[INFO] Checking required CLI tools..."
for cmd in kubectl helm; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "[ERROR] Required command '$cmd' not found in PATH." >&2
    exit 1
  fi
done

echo "[INFO] Ensuring namespace '${NAMESPACE}' exists with Restricted PSS labels..."
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -
kubectl label namespace "${NAMESPACE}" \
  pod-security.kubernetes.io/enforce=baseline \
  pod-security.kubernetes.io/warn=restricted \
  --overwrite

echo "[INFO] Adding prometheus-community Helm repository..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

echo "[INFO] Deploying ${RELEASE_NAME} via Helm..."
helm upgrade --install "${RELEASE_NAME}" prometheus-community/kube-prometheus-stack \
  --namespace "${NAMESPACE}" \
  -f "${VALUES_FILE}" \
  --wait --timeout 5m

echo "[INFO] Applying Zero-Trust NetworkPolicy for Prometheus scraping..."
kubectl apply -f monitoring/allow-prometheus-scraping.yaml

echo "[SUCCESS] Observability stack deployed and hardened."
