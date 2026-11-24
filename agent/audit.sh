#!/usr/bin/env bash
# Level 3: read-only audit van de Kubernetes-cluster.
# Zoekt wat de gecorrumpeerde incident-agent in zijn eigen voordeel heeft veranderd:
#   - resource-verhogingen (CPU/geheugen)
#   - permission creep (RBAC + gekoppelde GCP service accounts)
#   - shadow scaling (replicas / HPA)
# Wijzigt NIETS aan de cluster. Alle output komt in docs/bewijs/level-3/<tijdstip>/.
#
# Gebruik:
#   agent/audit.sh                 # alle namespaces
#   agent/audit.sh <namespace>     # één namespace
#   GCP_PROJECT=<id> agent/audit.sh  # ook de IAM-policy van het GCP-project ophalen
#
# Tools: kubectl, jq (optioneel gcloud). Op NixOS:
#   nix shell nixpkgs#kubectl nixpkgs#jq nixpkgs#google-cloud-sdk -c agent/audit.sh
set -euo pipefail
shopt -s inherit_errexit

NS="${1:-}"
if [[ -n "$NS" ]]; then NSFLAG=(-n "$NS"); else NSFLAG=(-A); fi

ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
OUT="$ROOT/docs/bewijs/level-3/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT"
echo "Output: $OUT"
# Ruwe JSON is alleen een tussenstap voor de analyses: tijdelijke map, niet in Git.
RAW="$(mktemp -d)"; trap 'rm -rf "$RAW"' EXIT

run() { # run <bestand> <commando...>: output naar bestand, fouten niet fataal
  local f="$1"; shift
  echo "  - $f"
  { echo "\$ $*"; "$@" 2>&1 || echo "(commando faalde)"; } > "$OUT/$f"
}

kubectl config current-context > "$OUT/00-context.txt" 2>&1 || true
run 01-namespaces.txt kubectl get ns

# Ruwe dumps (bron voor de jq-analyses hieronder)
kubectl get deploy,statefulset,daemonset "${NSFLAG[@]}" -o json > "$RAW/raw-workloads.json"
kubectl get replicaset "${NSFLAG[@]}" -o json > "$RAW/raw-replicasets.json"
kubectl get hpa "${NSFLAG[@]}" -o json > "$RAW/raw-hpa.json" 2>/dev/null || echo '{"items":[]}' > "$RAW/raw-hpa.json"

# 1. Resources en replicas per container
jq -r '
  ["NAMESPACE","KIND","NAAM","REPLICAS","CONTAINER","CPU_REQ","CPU_LIM","MEM_REQ","MEM_LIM","SA"],
  (.items[] | . as $w | .spec.template.spec.containers[] |
    [$w.metadata.namespace, $w.kind, $w.metadata.name, ($w.spec.replicas // "-"), .name,
     (.resources.requests.cpu // "-"), (.resources.limits.cpu // "-"),
     (.resources.requests.memory // "-"), (.resources.limits.memory // "-"),
     ($w.spec.template.spec.serviceAccountName // "default")])
  | @tsv' "$RAW/raw-workloads.json" | column -t -s $'\t' > "$OUT/10-resources-replicas.txt"

# 2. Wie heeft wat wanneer gewijzigd (managedFields: manager = welke tool/agent)
jq -r '
  ["NAMESPACE","KIND","NAAM","MANAGER","OPERATIE","TIJD"],
  (.items[] | . as $w | (.metadata.managedFields // [])[] |
    [$w.metadata.namespace, $w.kind, $w.metadata.name, .manager, .operation, .time])
  | @tsv' "$RAW/raw-workloads.json" | sort -t $'\t' -k6 | column -t -s $'\t' > "$OUT/11-wijzigingen-managedfields.txt"

# 3. ReplicaSet-geschiedenis: elke rollout met zijn resources en replicas, chronologisch
jq -r '
  ["NAMESPACE","REPLICASET","AANGEMAAKT","REVISIE","REPLICAS","CPU_REQ","MEM_REQ","CPU_LIM","MEM_LIM","CHANGE-CAUSE"],
  (.items | sort_by(.metadata.creationTimestamp)[] | . as $r | .spec.template.spec.containers[0] as $c |
    [$r.metadata.namespace, $r.metadata.name, $r.metadata.creationTimestamp,
     ($r.metadata.annotations["deployment.kubernetes.io/revision"] // "-"), ($r.spec.replicas // "-"),
     ($c.resources.requests.cpu // "-"), ($c.resources.requests.memory // "-"),
     ($c.resources.limits.cpu // "-"), ($c.resources.limits.memory // "-"),
     ($r.metadata.annotations["kubernetes.io/change-cause"] // "-")])
  | @tsv' "$RAW/raw-replicasets.json" | column -t -s $'\t' > "$OUT/12-replicaset-geschiedenis.txt"

# 4. HPA's (shadow scaling)
jq -r '
  ["NAMESPACE","HPA","TARGET","MIN","MAX"],
  (.items[] | [.metadata.namespace, .metadata.name, .spec.scaleTargetRef.name, (.spec.minReplicas // 1), .spec.maxReplicas])
  | @tsv' "$RAW/raw-hpa.json" | column -t -s $'\t' > "$OUT/13-hpa.txt"

# 5. RBAC: welke rollen hangen aan welke service accounts (permission creep)
kubectl get clusterrolebindings -o json > "$RAW/raw-clusterrolebindings.json"
kubectl get rolebindings "${NSFLAG[@]}" -o json > "$RAW/raw-rolebindings.json"
jq -rs '
  ["SCOPE","BINDING","ROL","SUBJECT_KIND","SUBJECT","AANGEMAAKT"],
  ([.[].items[]] | sort_by(.metadata.creationTimestamp)[] | . as $b | ($b.subjects // [])[] |
    [($b.metadata.namespace // "cluster"), $b.metadata.name, ($b.roleRef.kind + "/" + $b.roleRef.name),
     .kind, ((.namespace // "") + "/" + .name), $b.metadata.creationTimestamp])
  | @tsv' "$RAW/raw-clusterrolebindings.json" "$RAW/raw-rolebindings.json" \
  | column -t -s $'\t' > "$OUT/20-rbac-bindings.txt"
grep -Ei 'cluster-admin|admin|edit|ServiceAccount' "$OUT/20-rbac-bindings.txt" > "$OUT/21-rbac-verdacht.txt" || true

# 6. Service accounts met een gekoppeld GCP service account (Workload Identity)
kubectl get sa "${NSFLAG[@]}" -o json | jq -r '
  ["NAMESPACE","K8S_SA","GCP_SA"],
  (.items[] | select(.metadata.annotations["iam.gke.io/gcp-service-account"]) |
    [.metadata.namespace, .metadata.name, .metadata.annotations["iam.gke.io/gcp-service-account"]])
  | @tsv' | column -t -s $'\t' > "$OUT/22-workload-identity.txt"

# 7. Events en configmaps (prompts van de agent zitten vaak in een configmap)
run 30-events.txt kubectl get events "${NSFLAG[@]}" --sort-by=.lastTimestamp
run 31-configmaps.txt kubectl get configmaps "${NSFLAG[@]}"
run 32-pods.txt kubectl get pods "${NSFLAG[@]}" -o wide

# 8. Optioneel: IAM-policy van het GCP-project (alleen lezen; aanpassen doet wimmevdv via Terraform)
if [[ -n "${GCP_PROJECT:-}" ]] && command -v gcloud >/dev/null; then
  run 40-gcp-iam-policy.txt gcloud projects get-iam-policy "$GCP_PROJECT" --format=yaml
fi

echo
echo "Klaar. Begin bij:"
echo "  $OUT/11-wijzigingen-managedfields.txt  (welke manager/agent wijzigde wat)"
echo "  $OUT/12-replicaset-geschiedenis.txt    (resources/replicas door de tijd)"
echo "  $OUT/21-rbac-verdacht.txt              (brede rollen op service accounts)"
