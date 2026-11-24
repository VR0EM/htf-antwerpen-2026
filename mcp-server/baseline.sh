#!/usr/bin/env bash
# Level 4: leg de antwoorden van de MCP-server vast, met tijdstip.
# De logic bomb maakt de server slechter naarmate de dag vordert (10:00 ok, 14:00 slecht, 16:00 onbruikbaar).
# Draai dit dus ZO VROEG MOGELIJK en daarna opnieuw, om de degradatie aan te tonen.
# Na de fix draai je het opnieuw als bewijs dat de data weer klopt.
#
# Gebruik:
#   mcp-server/baseline.sh <MCP-URL> [calls-bestand]
#   Met basic auth: MCP_AUTH="guild:$(cd workload && terraform output -raw password)" mcp-server/baseline.sh <url>
#   bv. kubectl port-forward svc/<mcp-server> 8080:<poort> -n <ns>   (in een andere terminal)
#       mcp-server/baseline.sh http://localhost:8080/mcp
#
# calls-bestand: één JSON-object per regel: {"name":"<tool>","arguments":{...}}
#   Standaard: mcp-server/calls.jsonl. Bestaat dat niet, dan wordt enkel tools/list opgehaald.
#   Vul het aan met tools uit tools/list, bv. {"name":"list_pods","arguments":{"namespace":"default"}}
#
# Ondersteunt MCP "streamable HTTP" (JSON of SSE-antwoord). Tools: curl, jq.
set -euo pipefail
shopt -s inherit_errexit

URL="${1:?Gebruik: $0 <MCP-URL> [calls-bestand]}"
ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
CALLS="${2:-$ROOT/mcp-server/calls.jsonl}"
OUT="$ROOT/docs/bewijs/level-4/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT"
HDRS="$(mktemp)"; AUTH="$(mktemp)"; trap 'rm -f "$HDRS" "$AUTH"' EXIT
# Basic auth (bv. de ingress van workload/): MCP_AUTH="guild:<wachtwoord>". Via een bestand, niet zichtbaar in ps.
if [[ -n "${MCP_AUTH:-}" ]]; then printf "Authorization: Basic %s\n" "$(printf %s "$MCP_AUTH" | base64 -w0)" > "$AUTH"; fi
SESSION=""

rpc() { # rpc <method> <params-json>: print het JSON-resultaat
  local ID; ID=$(date +%s%N)   # uniek per call (rpc draait in een subshell)
  local body; body=$(jq -nc --arg m "$1" --argjson p "$2" --argjson id "$ID" '{jsonrpc:"2.0",id:$id,method:$m,params:$p}')
  local extra=(); [[ -n "$SESSION" ]] && extra=(-H "Mcp-Session-Id: $SESSION")
  local resp; resp=$(curl -sS -H @"$AUTH" -D "$HDRS" -X POST "$URL" \
    -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
    "${extra[@]}" --data "$body")
  if grep -q '^data: ' <<<"$resp"; then sed -n 's/^data: //p' <<<"$resp" | tail -1   # SSE
  else printf '%s\n' "$resp"; fi                                                     # gewone JSON
}

INIT=$(rpc initialize '{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"htf-baseline","version":"1"}}')
SESSION=$(grep -i '^mcp-session-id:' "$HDRS" | awk '{print $2}' | tr -d '\r' || true)
echo "$INIT" | jq . > "$OUT/00-initialize.json"
# initialized-notificatie (geen id, geen antwoord verwacht)
curl -sS -H @"$AUTH" -o /dev/null -X POST "$URL" -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  ${SESSION:+-H "Mcp-Session-Id: $SESSION"} --data '{"jsonrpc":"2.0","method":"notifications/initialized"}' || true

rpc tools/list '{}' | jq . > "$OUT/01-tools-list.json"
echo "Tools:"; jq -r '.result.tools[]? | "  - \(.name): \(.description // "" | .[0:80])"' "$OUT/01-tools-list.json"

if [[ -f "$CALLS" ]]; then
  n=0
  while IFS= read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    n=$((n + 1))
    name=$(jq -r .name <<<"$line")
    rpc tools/call "$line" | jq --arg t "$(date -Iseconds)" '. + {opgehaald: $t}' > "$OUT/$(printf %02d $((n + 1)))-$name.json"
    echo "  call $n: $name"
  done < "$CALLS"
fi

echo "Opgeslagen in $OUT"
echo "Vergelijk twee momenten met: diff -r docs/bewijs/level-4/<eerste> docs/bewijs/level-4/<laatste>"
