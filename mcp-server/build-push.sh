#!/usr/bin/env bash
# Level 4: bouw de Ancient Oracle-image en push ze naar de registry van het team,
# ZONDER Docker-daemon (die draait niet op onze laptop). We gebruiken `crane`.
#
# Wat dit doet is hetzelfde als workload/images/ancient-oracle/Dockerfile:
#   1. neem de officiële image python:3.13-alpine (voor linux/amd64, zoals de nodes)
#   2. voeg onze code toe als extra laag: /app/oracle/
#   3. zet de start-instellingen: env, workdir /app, user 65534, poort 8080,
#      entrypoint `python3 -m oracle`
#
# Gebruik (vanuit de repo-root, met de .env-bestanden ingeladen):
#   mcp-server/build-push.sh 1.0.1
# Daarna: ancient_oracle_tag = "1.0.1" in workload/terraform.tfvars en terraform apply.
#
# Tools: crane, terraform (op NixOS: nix shell nixpkgs#crane).
set -euo pipefail

TAG="${1:?Gebruik: $0 <tag>, bv. 1.0.1}"
ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
SRC="$ROOT/workload/images/ancient-oracle"

# Registry-gegevens uit de Terraform-outputs van core/ (wachtwoord gaat via stdin, nooit op het scherm)
cd "$ROOT/core"
REGISTRY=$(terraform output -raw registry_url | sed -E 's#^https?://##; s#/$##')
REG_USER=$(terraform output -raw registry_user)
terraform output -raw registry_password | crane auth login "$REGISTRY" -u "$REG_USER" --password-stdin

IMAGE="$REGISTRY/realm/ancient-oracle:$TAG"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

# Stap 2: onze code als laag (bestanden van root, leesbaar voor iedereen; geen __pycache__)
mkdir -p "$TMP/layer/app"
cp -r "$SRC/oracle" "$TMP/layer/app/oracle"
find "$TMP/layer" -name '__pycache__' -prune -exec rm -rf {} +
tar -C "$TMP/layer" --owner=0 --group=0 --mode='a+rX,go-w' -cf "$TMP/code.tar" app

# Stap 1 + 3: base-image + laag + instellingen, en meteen pushen
crane mutate python:3.13-alpine --platform linux/amd64 \
  --append "$TMP/code.tar" \
  -e PYTHONDONTWRITEBYTECODE=1 -e PYTHONUNBUFFERED=1 -e PYTHONIOENCODING=utf-8 \
  --workdir /app --user 65534:65534 --exposed-ports 8080 \
  --entrypoint python3,-m,oracle \
  -l "org.opencontainers.image.source=htf-antwerpen-2026" -l "htf.fix=level-4-tijdsbom-verwijderd" \
  -t "$IMAGE"

echo "Gepusht: $IMAGE"
crane config "$IMAGE" | jq -c '{arch: .architecture, entrypoint: .config.Entrypoint, user: .config.User, workdir: .config.WorkingDir}'
