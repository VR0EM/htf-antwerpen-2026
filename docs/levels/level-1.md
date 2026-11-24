# Level 1: Seal of the Ancient Scrolls (drift)

**Eigenaar:** Wimme · **Issue:** #5 · **Code:** `core/`

!!! info "Volledig rapport"
    Tijdlijn, alle 11 afwijkingen met beslissing en bewijs: [drift-rapport](../bewijs/level-1/drift-rapport.md).
    Uitleg over core/workload en de cluster: [architectuur](../architectuur.md).

## De opdracht in gewone taal

Iemand ("night-shift") heeft de cloud **met de hand** aangepast. Zoek alle verschillen tussen code en
werkelijkheid, beslis per verschil of het moet blijven, en maak dan de **code** de waarheid.

## Hoe vind je drift?

1. `terraform plan` in `core/`: alles wat Terraform beheert en afwijkt, staat in het plan.
2. **Ghost resources** zoeken: dingen die bestaan maar níet in de code staan. Die ziet `plan` niet.
   Je moet ze zelf opvragen (OVH-console in **lezen**-modus, of de OVH-API) en vergelijken met de code.

## Wat er gevonden werd

| Wat | Was (live) | Code zegt | Beslissing |
|---|---|---|---|
| IP-restrictie op de Kube-API | `198.51.100.0/24` (niemand kan erbij!) | niets | In code gezet, open, zodat elke wijziging voortaan drift is |
| `update_policy` cluster | `NEVER_UPDATE` | `MINIMAL_DOWNTIME` | Terug naar code |
| Nodepool min/max | 2 / 5 | 1 / 3 | max 3 terug; **min 2 bewust behouden** (overleeft uitval van 1 node) |
| Nodepool labels | `managed-by=console`, `owner=night-shift` | `managed-by=terraform` | Terug naar code |
| Bucket `scrolls` | versioning + encryptie **uit** | aan | Terug aan + `prevent_destroy` |
| S3-policy `scrolls_app` | `s3:*` op alles | alleen de eigen bucket | Terug naar least privilege |
| Gateway | groter model | model S | Terug naar code |
| Ghosts | hotfix-nodepool, `debug-admin` (administrator!), extra S3-key | (bestonden niet) | Eerst **importeren** in Terraform, daarna verwijderen |

!!! tip "Waarom eerst importeren en dan pas verwijderen?"
    Met `terraform import` zeg je: *"Dit ding bestaat, beheer het voortaan."* Daarna kun je het
    via de code verwijderen. Zo loopt **zelfs het opruimen** via Git en is het terug te zien in de geschiedenis.

## De beslissing "is deze handmatige wijziging nodig?"

Niet alles wat met de hand veranderd is, is slecht. Stel jezelf de vraag:

- Lost het een **echt probleem** op? (bv. min 2 nodes: anders ligt alles plat als één node uitvalt.) → **Opnemen in de code.**
- Is het **gemakzucht of een aanval**? (bv. `s3:*`, een admin-account "debug") → **Terugdraaien.**

## Nog te doen (Level 1)

- [x] Drift teruggezet via de code (#20) en ghosts verwijderd (#22): `plan` geeft *No changes*
- [ ] Pipeline: `terraform fmt -check`, `validate` en `plan` bij elke PR, `apply` alleen vanaf `main`
