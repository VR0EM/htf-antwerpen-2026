# Drift-rapport level 1: Seal of the Ancient Scrolls

**Team:** de-rubberen-badeendjes · **Eigenaar:** wimmevdv · **Issue:** #5 · **Code:** `core/`
**Status:** drift hersteld en ghosts verwijderd (24/11, ~11:30). De pipeline en de automatische drift-check volgen nog.

Uitleg over de omgeving en de diagrammen: [architectuur](../../architectuur.md).

## Samenvatting

Tussen ~10:57 en ~11:16 heeft "night-shift" ons OVH-project **via de console** aangepast, buiten Git om.
Een deel daarvan kon `terraform plan` zien (attributen van resources die Terraform beheert). Een ander deel
niet: een instelling die nooit in de code stond (de IP-restrictie) en drie ghost resources.
Gevolg: niemand kon nog bij de cluster, het project had een extra administrator en een extra VM, en de bucket
met de data van het rijk was niet langer versioned of encrypted.

Alles is teruggezet **via Git en Terraform**. Na de fix geeft `terraform plan` op `core/`: *No changes*.

## Tijdlijn (lokale tijd, CET)

| Tijd | Wat | Bron |
|---|---|---|
| 10:06–10:16 | FlowFactor zet het project op (state-bucket, core, workload) | aanmaakdata in de OVH-API |
| 10:45 | Eerste controle: `terraform plan` op core geeft *No changes*, de OVH-inventaris is schoon | onze eigen check |
| **10:57** | Nodepool `achrona-pool` aangepast (min/max, labels), ghost-nodepool **`hotfix-pool`** aangemaakt, **IP-restrictie** + **`NEVER_UPDATE`** op de cluster | `updatedAt`/`createdAt` in `01-ovh-api-kube.txt` |
| ~10:58 | `kubectl`: `Unable to connect to the server: EOF` | `03-kubectl-geblokkeerd.txt` |
| 11:02 | Gateway naar model **M**, gebruiker **`debug-admin`** (administrator) aangemaakt | OVH-API |
| ~11:0x | S3-policy `scrolls_app` naar `s3:*` op alles, extra S3-key voor `scrolls_app` | OVH-API |
| 11:16 | Bucket `scrolls`: versioning **SUSPENDED**, encryptie **uit** | `06-plan-fix-met-imports.txt` |
| 11:18–11:24 | Fix #20: drift terugzetten + ghosts importeren (APPLY START/KLAAR op #5) | `05-apply-…`, PR #20 |
| 11:20 | Kube-API weer bereikbaar, Dali kan verder | `kubectl get nodes` |
| 11:30 | Fix #22: ghosts verwijderd | `07-plan-ghosts-verwijderen.txt`, PR #22 |
| 11:35 | Controle: plan *No changes*, inventaris schoon | `20261124-1135-na-fix/` |

## Wat er afweek, en wat we beslisten

De opdracht vraagt per afwijking: *was de handmatige wijziging nodig?* Zo ja, dan nemen we ze op in de code.
Zo nee, dan draaien we ze terug.

| # | Resource | Code (Git) | Live (na night-shift) | Zag `plan` het? | Nodig? | Beslissing | Waar |
|---|---|---|---|---|---|---|---|
| 1 | IP-restrictie Kube-API | *(stond niet in de code)* | `198.51.100.0/24` (TEST-NET-2: sluit iedereen buiten) | **nee** | nee: legt alles plat | In code gezet (`ovh_cloud_project_kube_iprestrictions`), open `0.0.0.0/0`, zodat elke wijziging voortaan drift is | `core/kube.tf`, `core/variables.tf` |
| 2 | Cluster `update_policy` | `MINIMAL_DOWNTIME` | `NEVER_UPDATE` | ja | nee: geen security-patches meer | Teruggezet | `core/kube.tf` |
| 3 | Nodepool `min_nodes` | 1 | 2 | ja | **ja** | **Opgenomen in de code**: met anti-affinity en 2 nodes overleeft het rijk de uitval van 1 node | `core/variables.tf` |
| 4 | Nodepool `max_nodes` | 3 | 5 | ja | nee: kosten zonder reden | Teruggezet naar 3 | `core/variables.tf` |
| 5 | Nodepool-labels | `managed-by=terraform` | `managed-by=console`, `owner=night-shift` | ja | nee | Teruggezet | `core/main.tf` (`local.tags`) |
| 6 | Gateway | model `S` | model `M` | ja | nee: geen extra verkeer nodig | Teruggezet | `core/network.tf` |
| 7 | Bucket `scrolls` | versioning `ENABLED`, encryptie `AES256` | versioning `SUSPENDED`, encryptie uit | ja (maar wilde de bucket **vervangen**, zie valkuil) | nee: dataverlies- en lekrisico | Teruggezet, plus `prevent_destroy` | `core/storage.tf` |
| 8 | S3-policy `scrolls_app` | alleen bucket `scrolls` (8 acties) | `s3:*` op `arn:aws:s3:::*` (Sid `TempFixAllAccess`) | ja | nee: tegen least privilege | Teruggezet | `core/iam.tf` |
| 9 | **Ghost:** nodepool `hotfix-pool` | — | 1 extra b3-8-VM, alleen systeempods | **nee** | nee: kost geld, niets draait erop | Geïmporteerd, daarna verwijderd | #20 → #22 |
| 10 | **Ghost:** user `debug-admin` | — | rol **administrator** op het hele project + S3-key | **nee** | nee: achterdeur | Geïmporteerd, daarna verwijderd | #20 → #22 |
| 11 | **Ghost:** extra S3-key `scrolls_app` | 1 key (Terraform) | 2 keys | **nee** | nee: onbekende tweede sleutel | Geïmporteerd, daarna verwijderd | #20 → #22 |

Wat **niet** afweek (gecontroleerd): het netwerk en subnet, de registry en de registry-user, de lifecycle-regels
van de bucket, de state-user en zijn policy. Er waren geen extra instances, volumes, snapshots, load balancers
of clusters.

## Hoe we het oplosten (en waarom zo)

1. **Eerst begrijpen, dan aanraken.** We vergeleken alles **read-only** (`terraform plan`, de OVH-API, `kubectl`)
   en legden het bewijs vast vóór er iets veranderde (`20261124-1100-drift-ontdekt/`).
2. **De code is de waarheid.** We pasten niets aan in de console. Elke correctie is een commit in `core/`.
3. **Wat niet in de code stond, kwam erin.** De IP-restrictie werd een resource met een `import`-blok.
   Terraform adopteert de bestaande instelling en overschrijft ze daarna met de waarde uit de code.
4. **Ghosts in twee stappen.** Terraform kan enkel verwijderen wat het beheert:
   - PR #20 importeert `hotfix-pool`, `debug-admin` en de extra key (`core/ghosts.tf`), zonder iets te veranderen.
   - PR #22 verwijdert `ghosts.tf`, waarna `apply` precies die 3 resources vernietigt (plan: `3 to destroy`, verder niets).
   Zo staat zelfs het opruimen in de Git-geschiedenis.
5. **Eén apply tegelijk.** Voor en na elke apply een melding "APPLY START/KLAAR" op #5 (er is geen state locking).

### Valkuil: de bucket zou vervangen worden

Na de wijziging in de console gaf de API voor de bucket een leeg `object_lock`-blok (`mode = ""`) terug.
Dat is een instelling die je alleen bij het aanmaken kunt kiezen. Daardoor wilde de provider de bucket
**vervangen**: verwijderen en opnieuw aanmaken, met verlies van de data. We hebben dat niet laten gebeuren:

- `lifecycle { ignore_changes = [object_lock], prevent_destroy = true }` in `core/storage.tf`
- De eerste apply faalde daarna toch: de provider stuurde de lege `mode` mee en de API weigerde die
  (`05-apply-1-deels-gefaald.txt`).
- Opgelost met een **eenmalige, gedocumenteerde correctie van de state**: `object_lock` op `null` gezet
  (`terraform state pull` → bewerken → `state push`, met een back-up). Daarna `plan -refresh=false`, met als
  resultaat enkel versioning + encryptie + policy (`2 to change`). Een gewone refresh-`plan` daarna gaf *No changes*.

## Bewijs

| Map | Inhoud |
|---|---|
| `20261124-1100-drift-ontdekt/01-ovh-api-kube.txt` | cluster (`NEVER_UPDATE`), IP-restrictie `198.51.100.0/24`, beide nodepools |
| `…/02-terraform-plan-core.txt` | eerste plan met drift (update policy, nodepool) |
| `…/03-kubectl-geblokkeerd.txt` | `kubectl`: EOF |
| `…/04-ghost-node-hotfix-pool.txt` | pods op de ghost-node: enkel systeempods |
| `…/05-apply-1-deels-gefaald.txt` | eerste apply: IP, cluster en gateway gelukt, bucket faalt (object_lock) |
| `…/06-plan-fix-met-imports.txt` | volledig fix-plan: 4 imports, 7 wijzigingen, 0 vernietigingen |
| `…/07-plan-ghosts-verwijderen.txt` | plan van #22: precies 3 ghosts vernietigen |
| `20261124-1135-na-fix/01-ovh-api.txt` | toestand na de fix: alles volgens de code |
| `20261124-1135-na-fix/02-terraform-plan-core.txt` | `No changes. Your infrastructure matches the configuration.` |

## Nog te doen

- [ ] **Pipeline** (GitHub Actions): `fmt -check`, `validate`, `plan` bij een PR en `apply` alleen vanaf `main`,
  met één `concurrency`-groep (lost ook het ontbreken van state locking op).
- [ ] **Drift-check** op een schema (`plan -detailed-exitcode`), die een issue opent bij drift.
- [ ] **Ghost-check**: inventaris via de OVH-API (users, nodepools, S3-keys, instances) vergelijken met de state,
  want `plan` ziet ghosts niet.
- [ ] Drift in `workload/` (Kubernetes-objecten tegenover Helm) bekijken.
