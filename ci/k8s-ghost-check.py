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

Daarnaast Helm-drift: objecten die Helm beheert maar die nadien met de hand
gewijzigd zijn (`kubectl patch/edit/replace/...`), zoals de ConfigMap
`scrolls-ledger` die om de 20 min opgedreven werd (OOM-lus van scrolls-app).
Met --remediate wordt zo'n object teruggezet naar het manifest van de laatste
Helm-release (`kubectl replace`). Workloads worden enkel gemeld: die past ook de
scribe van Ixeth aan (via de grimoire), dat is geen hand-werk.

Gebruik:
  k8s-ghost-check.py core-state.json             # melden, exit 2 bij ghosts
  k8s-ghost-check.py core-state.json --remediate # en verwijderen
core-state.json = `terraform -chdir=core show -json` (daar zit de kubeconfig in).
De kubeconfig gaat naar een tijdelijk bestand (0600) en wordt nooit getoond.
"""

import base64
import gzip
import json
import os
import re
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


# --- Helm-drift ---------------------------------------------------------------

HAND = ("kubectl-patch", "kubectl-edit", "kubectl-replace", "kubectl-set", "kubectl-scale",
        "kubectl-label", "kubectl-annotate", "kubectl-client-side-apply")
FIXER = "k8s-ghost-check"   # field manager van onze eigen herstelling: telt als Helm


def releases():
    """Manifest-documenten van de laatste gedeployde release van elke Helm-release."""
    docs = {}
    out = json.loads(kubectl("get", "secrets", "-A", "-l", "owner=helm,status=deployed", "-o", "json"))
    for sec in out.get("items", []):
        raw = base64.b64decode(sec["data"]["release"])           # Kubernetes-base64
        rel = json.loads(gzip.decompress(base64.b64decode(raw)))  # Helm: base64 + gzip
        ns = rel.get("namespace", "")
        for doc in re.split(r"(?m)^---\s*$", rel.get("manifest", "")):
            kind = re.search(r"(?m)^kind:\s*(\S+)", doc)
            name = re.search(r"(?m)^metadata:\s*\n(?:\s+.*\n)*?\s{2}name:\s*['\"]?([^'\"\s]+)", doc)
            if not (kind and name):
                continue
            dns = re.search(r"(?m)^\s{2}namespace:\s*['\"]?([^'\"\s]+)", doc)
            docs[(kind.group(1), dns.group(1) if dns else ns, name.group(1))] = (rel["name"], doc)
    return docs


def hand_edited(obj):
    """De hand-manager als iemand het object na Helm met de hand wijzigde, anders None."""
    last_helm, hand = "", None
    for f in obj.get("metadata", {}).get("managedFields") or []:
        mgr, t = f.get("manager", ""), f.get("time", "")
        if mgr.startswith(("terraform-provider-helm", "helm")) or mgr == FIXER:
            last_helm = max(last_helm, t)
        elif mgr in HAND and (hand is None or t > hand[1]):
            hand = (mgr, t)
    return hand if hand and hand[1] > last_helm else None


def helm_drift(remediate):
    rows = []
    manifests = releases()
    for (kind, ns, name), (release, doc) in sorted(manifests.items()):
        args = ["get", kind, name, "-o", "json", "--show-managed-fields"] + (["-n", ns] if ns else [])
        try:
            obj = json.loads(kubectl(*args))
        except RuntimeError:
            continue  # bestaat niet (meer): helm zelf of de pipeline maakt het opnieuw
        if obj.get("metadata", {}).get("namespace", "") != ns and obj.get("metadata", {}).get("namespace"):
            continue
        hand = hand_edited(obj)
        if not hand:
            continue
        action = "gemeld"
        if remediate and kind not in ("Deployment", "DaemonSet", "StatefulSet"):
            p = subprocess.run(["kubectl", "replace", f"--field-manager={FIXER}", "-f", "-"] + (["-n", ns] if ns else []),
                               input=doc, capture_output=True, text=True, timeout=120)
            action = "**teruggezet naar Helm**" if p.returncode == 0 else f"terugzetten faalde: {p.stderr.strip()[:200]}"
        rows.append((kind, ns, name, release, f"{hand[0]} om {hand[1]}", action))
    return rows


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
        else:
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

        drift = helm_drift(remediate)
        print("\n### Helm-drift (met de hand gewijzigd na Helm)\n")
        if not drift:
            print("Geen gevonden.")
        else:
            print("| Soort | Namespace | Naam | Release | Gewijzigd door | Actie |")
            print("|---|---|---|---|---|---|")
            for kind, ns, name, release, who, action in drift:
                print(f"| {kind} | {ns or '-'} | `{name}` | {release} | {who} | {action} |")
        return 2 if ghosts or drift else 0
    finally:
        os.unlink(kc)


if __name__ == "__main__":
    sys.exit(main())
