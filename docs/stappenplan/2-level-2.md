# Fase 2: Level 2, gelekte sleutel (Wimme)

!!! warning "Nog niet uitgevoerd"
    Op het moment van schrijven (13:05) is Level 2 nog niet gestart. Dit is het **plan**, op basis van wat we al vonden.
    Wordt aangevuld zodra het gedaan is.

## Wat we al weten

- In `workload/charts/kube-monitoring/templates/scrolls.yaml` staat een **S3-sleutel in platte tekst** (Secret `scrolls-app-credentials`).
- `core/iam.tf` maakt al een nette user `scrolls_app` met een S3-sleutel die alleen de bucket `scrolls` mag gebruiken. Die wordt niet gebruikt.
- Night-shift had de policy van `scrolls_app` op `s3:*` gezet, plus een **extra S3-sleutel** en een user `debug-admin` (opgeruimd in L1).

## Stap 2.1: Indammen: de gelekte sleutel intrekken

**Doel:** de oude sleutel werkt nergens meer.

- Zoek bij welke OVH-user de sleutel hoort (OVH-API: `/cloud/project/<sn>/user/<id>/s3Credentials`).
- Verwijder of roteer hem **via Terraform** (de credential-resource vervangen met `terraform apply -replace=...`).

:white_check_mark: **Checkpoint (bewijs):** een request met de oude sleutel geeft `403`:

```bash
AWS_ACCESS_KEY_ID=<oud> AWS_SECRET_ACCESS_KEY=<oud> \
  aws s3 ls s3://<bucket> --endpoint-url https://s3.gra.io.cloud.ovh.net   # → AccessDenied / 403
```

:warning: **Nooit** de sleutel zelf in `docs/` zetten. Kort hem in (`9d4e1c7a...`).

## Stap 2.2: De app laten werken zonder sleutel in Git

**Doel:** `scrolls-app` krijgt de sleutel van `core/iam.tf`, via Terraform, niet via een bestand in Git.

Idee: in `workload/` een `kubernetes_secret_v1` maken met de credential uit de remote state van `core/`
(zoals `ancient.tf` dat al doet voor de registry), en de hardcoded Secret uit `scrolls.yaml` halen.

## Stap 2.3: Onderzoeken wat de aanvaller deed

- Bucket `scrolls`: welke objecten en versies zijn er? Wat is nieuw, gewijzigd of weg? (Versioning stond uit, en is in L1 terug aangezet.)
- OVH-logs of audit, voor zover beschikbaar: wanneer werd de sleutel gebruikt?
- Alles noteren in `docs/bewijs/level-2/` en terugdraaien via de code.

## Stap 2.4: Least privilege

Welke S3-acties gebruikt `scrolls-app` echt? Alleen die blijven in de policy van `core/iam.tf`.

:test_tube: **Probeer zelf:** lees `scrolls.yaml`. Wat doet de app met de bucket: lezen, schrijven, verwijderen?
Welke acties uit de policy zijn dan overbodig?
