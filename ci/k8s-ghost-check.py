#!/usr/bin/env python3
"""
Ghost-check voor de Kubernetes-laag (#57, VR0EM).

`terraform plan` en ci/ghost-check.py zien enkel OVH. Om 13:39 kwam er in de
cluster zelf een backdoor bij (cluster-admin voor de namespace `oracle`, een
deployment in kube-system die elke 2 minuten de grimoire vergiftigde) en de
drift-check bleef groen. Dit script zoekt objecten die niet door Helm, Terraform
of OVH beheerd worden en die er niet horen:

  1. RBAC met het label van de grimoire: de grimoire mag nooit rechten bezitten.
  2. (Cluster)RoleBindings buiten Helm die rechten geven aan service accounts in
     onze namespaces (ook via de groep system:serviceaccounts:<ns>).
  3. Workloads buiten Helm en de grimoire: in kube-system alles wat geen image
     van OVH (mks.kubernatine.ovh/) draait, in andere namespaces alles.
  4. ServiceAccounts buiten Helm in onze namespaces (behalve `default`).
  5. Alles wat met de hand `kubectl apply`'d is (annotatie last-applied-configuration):
     Helm, Terraform, OVH en de scribe (server-side apply) zetten die nooit.

Gebruik:
  k8s-ghost-check.py core-state.json             # melden, exit 2 bij ghosts
  k8s-ghost-check.py core-state.json --remediate # en verwijderen
core-state.json = `terraform -chdir=core show -json` (daar zit de kubeconfig in).
De kubeconfig gaat naar een tijdelijk bestand (0600) en wordt nooit getoond.
"""

import json
import os
import subprocess
import sys
import tempfile

OURS = {"scrolls", "observability", "oracle", "ancient", "traefik"}
SYSTEM_NS = {"kube-system", "kube-public", "kube-node-lease"}
OVH_IMAGE = "mks.kubernatine.ovh/"
REALM_LABEL = "grimoire.achrona.io/realm"
LAST_APPLIED = "kubectl.kubernetes.io/last-applied-configuration"

# Volgorde = volgorde van verwijderen: eerst wat draait (persistentie), dan rechten.
WORKLOADS = ["deployments.apps", "daemonsets.apps", "statefulsets.apps", "cronjobs.batch"]
BINDINGS = ["clusterrolebindings.rbac.authorization.k8s.io", "rolebindings.rbac.authorization.k8s.io"]
ROLES = ["clusterroles.rbac.authorization.k8s.io", "roles.rbac.authorization.k8s.io"]
OTHER = ["serviceaccounts", "configmaps", "secrets"]


def kubectl(*args):
    p = subprocess.run(["kubectl", *args], capture_output=True, text=True, timeout=120)
    if p.returncode != 0:
        raise RuntimeError(f"kubectl {' '.join(args[:3])}: {p.stderr.strip()[:300]}")
    return p.stdout


def items(kind):
    return json.loads(kubectl("get", kind, "-A", "-o", "json")).get("items", [])


def helm(md):
    return (md.get("labels") or {}).get("app.kubernetes.io/managed-by") == "Helm"


def touches_ours(subjects):
    for s in subjects or []:
        if s.get("kind") == "ServiceAccount" and s.get("namespace") in OURS:
            return True
        # Niet de groep van álle SA's: die gebruikt Kubernetes zelf (issuer-discovery).
        if s.get("kind") == "Group" and s.get("name", "").removeprefix("system:serviceaccounts:") in OURS:
            return True
    return False


def images(obj):
    spec = obj.get("spec", {})
    pod = spec.get("jobTemplate", {}).get("spec", spec).get("template", {}).get("spec", {})
    return [c.get("image", "") for c in pod.get("containers", []) + pod.get("initContainers", [])]


def why_ghost(kind, obj):
    md = obj.get("metadata", {})
    labels, ns = md.get("labels") or {}, md.get("namespace", "")
    if helm(md) or md.get("ownerReferences"):
        return None
    if LAST_APPLIED in (md.get("annotations") or {}):
        return "met de hand aangemaakt (kubectl apply)"
    if kind in BINDINGS + ROLES and labels.get(REALM_LABEL) == "true":
        return "RBAC uit de grimoire"
    if kind in BINDINGS and touches_ours(obj.get("subjects")):
        role = obj.get("roleRef", {}).get("name")
        return f"geeft {role} aan service accounts in onze namespaces"
    if kind in WORKLOADS and labels.get(REALM_LABEL) != "true":
        if ns == "kube-system":
            vreemd = [i for i in images(obj) if not i.startswith(OVH_IMAGE)]
            if vreemd:
                return f"geen OVH-image in kube-system ({', '.join(vreemd)})"
        elif ns not in SYSTEM_NS:
            return "workload buiten Helm"
    if kind == "serviceaccounts" and ns in OURS and md.get("name") != "default":
        return "service account buiten Helm"
    return None


def kubeconfig_from_state(path):
    with open(path) as f:
        state = json.load(f)
    for r in state.get("values", {}).get("root_module", {}).get("resources", []):
        if r.get("address") == "ovh_cloud_project_kube.this":
            return r["values"]["kubeconfig"]
    raise SystemExit("geen ovh_cloud_project_kube.this in de state")


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    remediate = "--remediate" in sys.argv[2:]
    fd, kc = tempfile.mkstemp(prefix="kubeconfig-")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(kubeconfig_from_state(sys.argv[1]))
        os.environ["KUBECONFIG"] = kc

        ghosts = []
        for kind in WORKLOADS + BINDINGS + ROLES + OTHER:
            for obj in items(kind):
                why = why_ghost(kind, obj)
                if why:
                    md = obj["metadata"]
                    ghosts.append((kind, md.get("namespace", ""), md["name"], md.get("creationTimestamp", ""), why))

        print("### Kubernetes-ghosts (buiten Helm, Terraform en OVH)\n")
        if not ghosts:
            print("Geen gevonden.")
            return 0
        print("| Soort | Namespace | Naam | Aangemaakt | Waarom | Actie |")
        print("|---|---|---|---|---|---|")
        for kind, ns, name, created, why in ghosts:
            action = "gemeld"
            if remediate:
                args = ["delete", kind, name, "--wait=false", "--ignore-not-found"]
                if ns:
                    args += ["-n", ns]
                try:
                    kubectl(*args)
                    action = "**verwijderd**"
                except RuntimeError as e:
                    action = f"verwijderen faalde: {e}"
            print(f"| {kind.split('.')[0]} | {ns or '-'} | `{name}` | {created} | {why} | {action} |")
        return 2
    finally:
        os.unlink(kc)


if __name__ == "__main__":
    sys.exit(main())
