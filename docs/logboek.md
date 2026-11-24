# Logboek

Elke wijziging, apply, vondst of beslissing van ons team: **wat**, **waarom**, **waar**, en eventuele **debug-info**.
Beide agents (wimmevdv en VR0EM) schrijven hier mee, in dezelfde PR als de wijziging. **Nieuwste entry bovenaan.**

Sjabloon:

```markdown
### HH:MM · <wie> · <korte titel>
- **Wat:** wat er veranderd is of gevonden werd
- **Waarom:** de reden of beslissing
- **Waar:** PR #.., issue #.., bestanden
- **Debug:** (optioneel) wat faalde en hoe het is opgelost
```

---

## 24 november 2026

### 11:55 · wimmevdv · Logboek opgezet
- **Wat:** dit logboek gemaakt en de regel "elke wijziging in het logboek" toegevoegd aan het protocol in `CLAUDE.md`.
- **Waarom:** twee agents die niet rechtstreeks praten. Zo weet elke agent wat de andere deed en waarom, en is debuggen makkelijker.
- **Waar:** issue #27.

### 11:40 · wimmevdv · Docs: architectuur en drift-rapport level 1
- **Wat:** `docs/architectuur.md` (diagrammen: het grote plaatje, core tegenover workload, de cluster in detail, de request-flow, drift voor/na) en `docs/bewijs/level-1/drift-rapport.md` (tijdlijn, 11 afwijkingen met beslissing, bewijsbestanden).
- **Waarom:** uitleg voor team, jury en de andere agent. Het rapport is ook het bewijs voor de pitch.
- **Waar:** PR #25, issue #19.

### 11:30 · wimmevdv · Ghosts verwijderd (APPLY core)
- **Wat:** `core/ghosts.tf` verwijderd. De apply vernietigde precies 3 resources: nodepool `hotfix-pool`, user `debug-admin` (administrator) en een extra S3-key van `scrolls_app`.
- **Waarom:** ghost resources horen niet in het rijk. Via Git verwijderen houdt ook het opruimen traceerbaar.
- **Waar:** PR #22, issue #5. Daarna geeft `plan` op core: *No changes*.
- **Debug:** op de ghost-node draaiden alleen systeempods (`docs/bewijs/level-1/…/04-ghost-node-hotfix-pool.txt`), dus verwijderen was veilig.

### 11:20 · wimmevdv · Drift hersteld + ghosts geadopteerd (APPLY core)
- **Wat:**
  - IP-restrictie van de Kube-API in code gezet (`ovh_cloud_project_kube_iprestrictions` + `import`, waarde `0.0.0.0/0`).
  - `update_policy`, nodepool (max 3, labels), gateway (S), bucket (versioning + encryptie) en S3-policy `scrolls_app` teruggezet naar de code.
  - `min_nodes` 2 **bewust** in de code opgenomen.
  - Ghosts geïmporteerd in `core/ghosts.tf`.
- **Waarom:** de code is de enige waarheid. Ghosts moeten eerst in de state komen voordat Terraform ze kan verwijderen. Min 2 nodes laat het rijk de uitval van één node overleven.
- **Waar:** PR #20, issue #5.
- **Debug:**
  1. De bucket wilde **vervangen** worden door een quirk van de provider (de API geeft na de wijziging in de console een leeg `object_lock`-blok terug). Opgelost met `ignore_changes = [object_lock]` en `prevent_destroy`, en daarna een eenmalige correctie van de state (`object_lock` op `null`, met een back-up), gevolgd door `plan -refresh=false`.
  2. Een wijziging aan de IP-restrictie zet de cluster een tijd op `REDEPLOYING`. De nodepool-update faalde daardoor eerst, en lukte daarna wel.

### 11:10 · wimmevdv · Meer drift + ghosts gevonden
- **Wat:**
  - bucket `scrolls` met versioning SUSPENDED en encryptie uit;
  - S3-policy `scrolls_app` op `s3:*` voor alle buckets;
  - gateway op model M;
  - ghosts: `hotfix-pool`, `debug-admin` en een extra S3-key.
- **Waarom belangrijk:** night-shift bleef live wijzigen (golven om 10:57, 11:02 en 11:16). `terraform plan` ziet ghosts niet, dus de OVH-API-inventaris is nodig.
- **Waar:** `docs/bewijs/level-1/20261124-1100-drift-ontdekt/`.

### 10:58 · wimmevdv · Kube-API onbereikbaar: drift
- **Wat:** `kubectl` gaf `EOF`. Oorzaak: een IP-restrictie `198.51.100.0/24` (TEST-NET-2) op de Kube-API, gezet via de console en niet in Terraform. Ook `NEVER_UPDATE` en een nodepool van 2/5 met de labels `owner=night-shift`.
- **Waarom belangrijk:** dit blokkeerde Dali (L3/L4) en elke apply op `workload/`.
- **Waar:** gemeld op #5 en #7 (`needs-sync`).

### 10:45 · wimmevdv · Setup en eerste verkenning
- **Wat:** terraform en helm geïnstalleerd, credentials lokaal gezet (gitignored), read-only `plan` op core en workload, OVH-inventaris via de API (alles was toen nog schoon). `*.zip` in `.gitignore`, omdat de FlowFactor-zip secrets bevat.
- **Waarom:** eerst begrijpen wat er staat, voor er iets verandert.
- **Waar:** PR #15.

<!-- VR0EM: vul hieronder (of op de juiste plaats in de tijd) je eigen entries aan, bv. #11, #13, #16, #17, #18, #23, #24, #26. -->
