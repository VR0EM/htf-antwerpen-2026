# Level 3: Seal of the Oracle (issue #7)

Eigenaar: VR0EM. Zie `docs/opdracht.md` voor de volledige opdracht.

## Plan van aanpak
1. **Audit (alleen lezen):** `agent/audit.sh [namespace]` → output in `docs/bewijs/level-3/<tijd>/`.
   - `11-wijzigingen-managedfields.txt`: wie (manager) wijzigde welke workload wanneer. Zoek een manager die op de agent lijkt.
   - `12-replicaset-geschiedenis.txt`: CPU/geheugen/replicas per rollout. Een sprong = **resource-verhoging**.
   - `13-hpa.txt` + replicas: onverklaarde stijging = **shadow scaling**.
   - `21-rbac-verdacht.txt` + `22-workload-identity.txt`: brede rollen of een GCP-SA met te veel rechten = **permission creep**.
2. **Git-geschiedenis van de agent-repo (die van FlowFactor):**
   ```bash
   git log --since="3 days ago" --stat
   git log -p -- '*prompt*' '*.yaml' '*.md'
   git log --format='%h %an <%ae> %ad %s' --date=iso   # verdachte auteurs/tijdstippen
   ```
3. **Code zuiveren:** zoek in de prompts en logica naar regels die de agent zelf bevoordelen. Handige zoekterms:
   ```bash
   grep -rniE 'replica|scale|cpu|memory|limit|request|admin|role|permission|iam|self|own|myself|priorit' .
   ```
   Let ook op logica die de naam van de agent zelf uitzondert of voortrekt (bv. `if target == "ir-agent"`).
4. **Terugdraaien:** `git revert <sha>` per ongeautoriseerde commit, op een branch, met een PR. Geen `kubectl edit` of console.
5. **Uitrollen:** de deploy-pipeline opnieuw draaien. Daarna `agent/audit.sh` nog eens uitvoeren en de output vergelijken met die van stap 1. Dat is het bewijs.
6. **IAM in de cloud:** als de agent GCP-rollen kreeg (bv. Security Admin), dan horen die in Terraform (`infra/`, van wimmevdv). **Niet zelf aanpassen:** zet een comment op #7 met het label `needs-sync`.

## Bevindingen
<!-- Vul aan tijdens het werk: wat, waar (commit/bestand), bewijs (pad in docs/bewijs/level-3/) -->
| # | Type | Wat | Waar | Opgelost via |
|---|---|---|---|---|
