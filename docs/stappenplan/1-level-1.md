# Fase 1: Level 1, drift (Wimme)

Volledig rapport: [drift-rapport](../bewijs/level-1/drift-rapport.md). Hier de stappen om het zelf te doen.

## Stap 1.1: Merken dat er iets mis is

Om 10:58 gaf `kubectl` plots dit:

```text
Unable to connect to the server: EOF
```

**Denk:** de ingress (`http://<ip>/`) werkte nog, dus de nodes leefden. Alleen de **API** sloot de verbinding.
Dat wijst op een netwerk- of toegangsregel, niet op een kapotte cluster.

## Stap 1.2: Vergelijken: code tegenover werkelijkheid

**A. Wat Terraform beheert**: `plan` toont de afwijkingen:

```bash
cd core && terraform plan
```

**B. Wat Terraform níet beheert**: vraag het rechtstreeks aan de OVH-API:

```bash
TOKEN=$(curl -s https://www.ovh.com/auth/oauth2/token \
  --data-urlencode grant_type=client_credentials \
  --data-urlencode "client_id=$OVH_CLIENT_ID" --data-urlencode "client_secret=$OVH_CLIENT_SECRET" \
  --data-urlencode scope=all | jq -r .access_token)
A=https://eu.api.ovh.com/1.0/cloud/project/<service_name>
curl -s -H "Authorization: Bearer $TOKEN" $A/kube/<kube_id>/ipRestrictions
curl -s -H "Authorization: Bearer $TOKEN" $A/kube/<kube_id>/nodepool | jq '.[] | {name, status}'
curl -s -H "Authorization: Bearer $TOKEN" $A/user | jq '.[] | {id, description, roles}'
```

:white_check_mark: **Checkpoint:** je vindt `ipRestrictions = ["198.51.100.0/24"]` (TEST-NET-2: niemand mag erbij),
een extra nodepool `hotfix-pool` en een user `debug-admin` met rol administrator.

:warning: **Valkuil:** `plan` ziet **ghosts niet**. Dingen die niet in de code staan, bestaan voor Terraform niet.
Je moet zelf een inventaris maken (later geautomatiseerd in `ci/ghost-check.py`).

## Stap 1.3: Per afwijking beslissen

Stel bij elke afwijking de vraag uit de opdracht: **"was deze handmatige wijziging nodig?"**

| Ja, nodig | Nee, terugdraaien |
|---|---|
| `min_nodes = 2`: overleeft de uitval van 1 node → **in de code** | `NEVER_UPDATE`, `s3:*`, gateway M, versioning uit, IP-lock |

:test_tube: **Probeer zelf:** bekijk de 11 rijen in het [drift-rapport](../bewijs/level-1/drift-rapport.md#wat-er-afweek-en-wat-we-beslisten). Zou jij overal hetzelfde beslissen?

## Stap 1.4: Wat niet in de code stond, erin zetten (import)

De IP-restrictie werd een resource. Met een `import`-blok adopteert Terraform de bestaande instelling
en overschrijft ze daarna met de waarde uit de code:

```hcl title="core/kube.tf"
resource "ovh_cloud_project_kube_iprestrictions" "this" {
  service_name = var.service_name
  kube_id      = ovh_cloud_project_kube.this.id
  ips          = var.kube_api_allowed_cidrs   # open: 0.0.0.0/0
}

import {
  to = ovh_cloud_project_kube_iprestrictions.this
  id = "${var.service_name}/${ovh_cloud_project_kube.this.id}"
}
```

## Stap 1.5: Ghosts opruimen in 2 PR's

1. **PR 1 (`ghosts.tf`):** de ghosts importeren, zonder iets te veranderen. Nu "kent" Terraform ze.
2. **PR 2:** `ghosts.tf` verwijderen. `plan` toont dan **exact 3 to destroy**, en niets anders.

**Waarom zo omslachtig?** Zo staat zelfs het opruimen in Git, met een review.

## Stap 1.6: Applyen, met melding

```bash
gh issue comment 5 --body "APPLY START core"
terraform plan -out=tfplan        # lees het plan!
terraform apply tfplan
gh issue comment 5 --body "APPLY KLAAR core"
```

:white_check_mark: **Checkpoint:** daarna geeft `terraform plan`: *No changes. Your infrastructure matches the configuration.*

:warning: **Valkuil: de bucket wilde vervangen worden.** Na de wijziging in de console gaf OVH een leeg `object_lock`-blok terug,
en de provider wilde de bucket **verwijderen en opnieuw aanmaken** (dataverlies!). De oplossing:
`lifecycle { ignore_changes = [object_lock], prevent_destroy = true }` en een eenmalige, gedocumenteerde correctie
van de state. **Lees een plan altijd: "must be replaced" bij een databron is een rood licht.**

:warning: **Valkuil: een wijziging aan de IP-restrictie zet de cluster even op `REDEPLOYING`.** Een nodepool-update
in dezelfde apply faalt dan. Gewoon opnieuw proberen.
