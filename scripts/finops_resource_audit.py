#!/usr/bin/env python3
"""
Kubernetes FinOps & Resource Governance Auditor
Scans cluster workloads (or YAML manifests) for missing CPU/Memory requests and limits
to prevent cloud cost overruns and noisy-neighbor resource exhaustion.
"""

import sys
import json
import argparse
from pathlib import Path
import yaml

def audit_manifest_file(filepath: Path) -> list:
    findings = []
    with open(filepath, "r", encoding="utf-8") as f:
        docs = list(yaml.safe_load_all(f))

    for doc in docs:
        if not doc or not isinstance(doc, dict):
            continue
        kind = doc.get("kind", "")
        if kind not in ["Deployment", "StatefulSet", "DaemonSet", "Pod"]:
            continue

        metadata = doc.get("metadata", {})
        name = metadata.get("name", "unknown")
        namespace = metadata.get("namespace", "default")

        spec = doc.get("spec", {})
        if kind != "Pod":
            spec = spec.get("template", {}).get("spec", {})

        containers = spec.get("containers", [])
        for c in containers:
            c_name = c.get("name", "unknown")
            resources = c.get("resources", {})
            requests = resources.get("requests", {})
            limits = resources.get("limits", {})

            missing = []
            if not requests.get("cpu"):
                missing.append("requests.cpu")
            if not requests.get("memory"):
                missing.append("requests.memory")
            if not limits.get("cpu"):
                missing.append("limits.cpu")
            if not limits.get("memory"):
                missing.append("limits.memory")

            if missing:
                findings.append({
                    "file": str(filepath),
                    "kind": kind,
                    "namespace": namespace,
                    "workload": name,
                    "container": c_name,
                    "missing_Allocations": missing,
                    "finops_impact": "HIGH - Unbounded resource consumption / cost allocation blindspot"
                })
    return findings

def main():
    parser = argparse.ArgumentParser(description="FinOps Kubernetes Resource Quota & Cost Governance Auditor")
    parser.add_argument("--path", default=".", help="Directory or YAML file to scan")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 if violations are found (CI gate)")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    target = Path(args.path)
    yaml_files = [target] if target.is_file() else list(target.rglob("*.yaml")) + list(target.rglob("*.yml"))

    all_findings = []
    for yf in yaml_files:
        if ".github" in str(yf) or "kube-prometheus-values" in str(yf):
            continue
        try:
            all_findings.extend(audit_manifest_file(yf))
        except Exception as exc:
            print(f"[WARN] Skipping {yf}: {exc}", file=sys.stderr)

    if args.json:
        print(json.dumps({"violations_count": len(all_findings), "findings": all_findings}, indent=2))
    else:
        print(f"=== FinOps & Resource Governance Audit Report ===")
        print(f"Scanned YAML files: {len(yaml_files)} | Violations found: {len(all_findings)}\n")
        for idx, item in enumerate(all_findings, 1):
            print(f"[{idx}] {item['kind']}/{item['workload']} (container: {item['container']}) in {item['file']}")
            print(f"    Missing: {', '.join(item['missing_Allocations'])}")
            print(f"    Impact : {item['finops_impact']}\n")

    if args.strict and all_findings:
        sys.exit(1)

if __name__ == "__main__":
    main()
