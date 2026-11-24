# Fase 5: Pipeline en zelfherstel

**Doel:** na deze fase applyt **niemand** nog met de hand. Git is de enige weg naar de cloud.

## Stap 5.1: Pipeline `infra.yml` (Wimme)

| Wanneer | Wat |
|---|---|
| Pull request | `terraform fmt -check`, `validate`, `plan` op `core/` en `workload/`. Het plan komt als comment op de PR |
| Push op `main` | `apply`: eerst `core/`, dan ghosts opruimen, dan `workload/` |
| Handmatig | `gh workflow run infra.yml --ref main` = "zet alles terug zoals op main" |

Alle applies zitten in **één concurrency-groep**. Dat vervangt de ontbrekende state locking.

De secrets (`OVH_*`, `AWS_*`) staan in GitHub Secrets, nooit in de repo.

## Stap 5.2: Drift-check `drift.yml` (Wimme)

Elke ±5 minuten (elke run start de volgende): `plan -detailed-exitcode` op beide stacks, `ci/ghost-check.py`
(de OVH-API tegenover de state) en `ci/k8s-ghost-check.py` (objecten in de cluster buiten Helm, en Helm-objecten die
met de hand gewijzigd zijn). Bij drift: een issue met label `drift`, en een apply-run (zelfherstel).

## Stap 5.3: Tests voor L3/L4 `l3-l4-tests.yml` (Dali)

Bij elke PR die charts, images, `agent/` of `mcp-server/` raakt: de tests + `helm lint`. Komt de corruptie terug, dan wordt de PR rood.

## Wat we leerden van de golven van night-shift

| Golf | Wat | Les |
|---|---|---|
| 10:57 | IP-lock, nodepool, ghosts, bucket, policy | `plan` ziet ghosts niet, dus een inventaris via de API is nodig |
| 11:34–11:41 | **Originele zip-code opnieuw geapplyd** (onze fixes weg), IP-lock, ghost | Detectie alleen is niet genoeg, herstel moet automatisch |
| 12:43–12:44 | IP-lock, ghost `hotfix-pool` (blijft lang `INSTALLING`), bucket | zie de valkuilen hieronder |
| 13:39 | Aanval **in** de cluster (Level 3 opnieuw), niet in OVH | De drift-check moet ook de Kubernetes-laag zien: `ci/k8s-ghost-check.py` |

:warning: **Valkuil: de geplande drift-check startte nooit.** GitHub start `schedule`-workflows met vertraging,
of de eerste keer helemaal niet. Vertrouw er niet blind op. Controleer met `gh run list --workflow drift.yml`.

:warning: **Valkuil: één fout blokkeert alles.** In `infra.yml` worden "ghosts opruimen" en "apply workload" overgeslagen als
`apply core` faalt. Een `object_lock`-quirk van de bucket hield zo het herstel van Level 3/4 tegen.

:warning: **Valkuil: OVH weigert een IP-restrictie aan te passen zolang een nodepool `INSTALLING` is.** De ghost-nodepool
van night-shift blokkeerde zo het openzetten van de API.

:test_tube: **Probeer zelf:** bekijk een run in het Actions-tabblad. Waar zie je het plan? Wat gebeurt er als je in een PR
een `.tf`-bestand slecht formatteert?
