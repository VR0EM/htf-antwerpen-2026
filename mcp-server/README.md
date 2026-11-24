# Level 4 (bonus): Seal of the Echo (issue #8)

Eigenaar: VR0EM. Zie `docs/opdracht.md` voor de volledige opdracht.

## ⏰ Eerst: baseline vastleggen (tijdgevoelig!)
De server degradeert met de klok (10:00 ok → 14:00 slecht → 16:00 onbruikbaar).
Zodra er toegang is, **meteen** de baseline nemen, ook als je nog aan Level 3 werkt:
```bash
kubectl get svc -A | grep -i mcp                      # service en poort vinden
kubectl port-forward -n <ns> svc/<mcp-svc> 8080:<poort>
mcp-server/baseline.sh http://localhost:8080/mcp      # pad kan /mcp of /sse zijn
```
Vul daarna `mcp-server/calls.jsonl` met een paar vaste tool-calls (zie `tools/list`) en draai het script elk uur opnieuw.

## Plan van aanpak
1. **Diagnose:** vergelijk de snapshots in `docs/bewijs/level-4/` met elkaar en met de eerdere logs van FlowFactor.
2. **Broncode inspecteren:** zoek naar tijd- of klokgebaseerde logica:
   ```bash
   grep -rniE 'time\.|datetime|date\.now|Date\(|getHours|hour|clock|now\(\)|sleep|random|rand|noise|jitter|shuffle|degrad' .
   git log -p -S 'hour' --all          # wanneer is de bom toegevoegd?
   ```
   Typisch patroon: `if hour >= 14: <ruis toevoegen / data inkorten / generiek antwoord>`.
3. **Verwijderen:** de bom eruit halen op een branch, met een PR. Liefst ook een test die de klok vastzet op 16:00 en controleert dat de output gelijk is aan die van 10:00.
4. **Rebuild en deploy:** nieuwe image bouwen met een nieuwe tag (niet `latest`), pushen naar de registry en uitrollen via de pipeline of het manifest in Git.
5. **Verifiëren:** `baseline.sh` opnieuw draaien en de output vergelijken met de baseline van de ochtend. Dat is het bewijs voor de pitch.

## Bevindingen
<!-- Bestand + regel van de bom, commit die hem toevoegde, commit die hem verwijdert, image-tag van de fix -->
