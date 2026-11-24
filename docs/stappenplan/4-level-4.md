# Fase 4: Level 4, tijdsbom in de MCP-server (Dali)

Uitleg met code: [Level 4](../levels/level-4.md). Hier de stappen.

## Stap 4.1: Bewijs nemen **vóór 12:00**

Het probleem wordt erger met de klok. Neem dus eerst een "foto" van de goede toestand:

```bash
MCP_AUTH="guild:$(cd workload && terraform output -raw password)" \
  mcp-server/baseline.sh http://<ingress-ip>/mcp          # → docs/bewijs/level-4/<tijd>/
```

:white_check_mark: **Checkpoint:** 8 tools, en tellingen die kloppen met `kubectl get pods -A | wc -l`.

:warning: **Valkuil:** in welke tijdzone draait de server? Bij ons stond `TZ` in de chart op Brussel. 12:00 was dus echt 12:00 bij ons.

## Stap 4.2: Zoeken naar alles wat met tijd of toeval werkt

```bash
grep -rnE 'random|time\.|localtime|hour|sleep' workload/images/ancient-oracle/
cat workload/images/ancient-oracle/Dockerfile                   # wat wordt waar gekopieerd?
```

:test_tube: **Probeer zelf:** vind de **3 plekken** voor je de [oplossing](../levels/level-4.md#stap-2-zoeken-naar-alles-wat-met-de-klok-te-maken-heeft) leest.
Tip: welk bestand laadt Python **automatisch** als het in `site-packages` staat?

## Stap 4.3: Weghalen

1. `runtime/sitecustomize.py` weg + de `COPY runtime/`-regel uit de Dockerfile.
2. `shaping.py`: alleen sorteren, niets weggooien of veranderen.
3. `server.py`: `GUIDANCE` weg.

## Stap 4.4: Testen met een nagebootste klok

```bash
python3 -m unittest discover -s mcp-server/tests -v
```

De test zet de klok op 10:30, 13:00, 15:45 en 16:30. Origineel: 0, 2, 17 en 21 van de 30 antwoorden fout. Gefixt: 0.

:warning: **Valkuil:** onze eerste test stond per ongeluk op 10:07 in plaats van 16:30 (foute TZ-notatie), en "slaagde" dus voor niets.
**Controleer altijd of je test ook faalt op de oude code.**

## Stap 4.5: Image bouwen en pushen

Met Docker:

```bash
docker build --platform linux/amd64 -t <registry>/realm/ancient-oracle:1.0.1 workload/images/ancient-oracle
docker push <registry>/realm/ancient-oracle:1.0.1
```

Zonder Docker-daemon (zoals bij ons): `mcp-server/build-push.sh 1.0.1` (met crane).

Daarna in `workload/terraform.tfvars`: `ancient_oracle_tag = "1.0.1"`. **Nooit `latest`**: met een vaste tag weet je wat er draait.

## Stap 4.6: Uitrollen en verifiëren

Via een PR → merge → pipeline. Daarna:

```bash
kubectl get deploy ancient-oracle -n ancient -o jsonpath='{..image}'     # ...:1.0.1
mcp-server/baseline.sh http://<ingress-ip>/mcp                           # na 12:00: zelfde als 10:45?
```

:test_tube: **Probeer zelf:** je kunt de live versie ook controleren **zonder** Kubernetes-toegang: vraag het aan de MCP-server zelf
(`list_deployments` in namespace `ancient`). Zo vonden wij om 11:47 dat 1.0.0 weer draaide.
