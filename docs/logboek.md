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

### 13:20 · wimmevdv · Vierde golf: pipeline robuuster (bucket, stappen na fout, drift-lus)
- **Wat:**
  - Vierde golf om 12:43–12:44: IP-lock, `NEVER_UPDATE`, nodepool, S3-policy, bucket weer `plaintext`, opnieuw `hotfix-pool`. De drift-check zag het en startte zelfherstel. De runs 45387916057 en 45388130560 faalden: de object_lock-bug van de bucket, en een IP-wijziging die geblokkeerd werd zolang `hotfix-pool` INSTALLING was.
  - Fix 1, bucket: van `ovh_cloud_storage_object_bucket` (v2-API, met de bug) naar `ovh_cloud_project_storage` (v1-API), met `removed { destroy = false }` en `import`. De bucket blijft bestaan (plan: 1 import, 0 destroy). Geen handmatige state-correcties meer.
  - Fix 2, `infra.yml`: "Ghosts opruimen" nu **vóór** de core-apply. Die stap en "Apply workload" lopen ook als een eerdere stap faalt (`!cancelled()`).
  - Fix 3, `drift.yml`: de `schedule` van GitHub heeft vandaag **nooit** gedraaid (0 geplande runs). Elke run start zichzelf daarom na 4 min opnieuw (tot 18:00 Belgische tijd). De cron (nu `*/10`) blijft als vangnet.
- **Waarom:** bij elke golf moet de pipeline zonder ingreep van een mens kunnen herstellen. Dali signaleerde de bucket-fout (#5).
- **Waar:** issue #47.

### 13:07 · VR0EM · Pages-workflow in 2 jobs
- **Wat:** `docs.yml` opgesplitst in `build` (upload) en `deploy` (`needs: build`), zoals het officiële Pages-voorbeeld.
- **Waarom:** in één job vond `deploy-pages` het artefact vaak niet (6x "No artifacts named github-pages"), terwijl de upload lukte en githubstatus "operational" zei. Een rerun hielp soms, niet altijd.
- **Waar:** deze PR.

### 13:05 · VR0EM · Stappenplan in het handboek
- **Wat:** sectie `docs/stappenplan/` met 7 pagina's (voorbereiding, L1–L4, pipeline, bewijs en pitch). Per stap: doel, commando's, checkpoint, valkuil en "probeer zelf". L1 gebaseerd op het drift-rapport van wimmevdv, L2 als **plan** (nog niet uitgevoerd).
- **Waarom:** het team moet alles stap voor stap kunnen naspelen en zelf proberen.
- **Waar:** deze PR.

### 12:59 · VR0EM · Derde drift-golf: infra.yml gestart, deels hersteld
- **Wat:** om 12:43 opnieuw IP-lock `198.51.100.0/24` en om 12:44 opnieuw de ghost `hotfix-pool`. Ook de ingress gaf geen antwoord meer. De geplande drift-check (`*/30`) was nog nooit gestart. Daarom `infra.yml` via workflow_dispatch op `main` gestart (akkoord Dali, APPLY START op #5). Resultaat: gateway, update_policy en nodepool hersteld. **IP-restrictie en bucket mislukt**, dus ghost-opruiming en workload-apply niet gedraaid.
- **Waarom:** de herstelweg uit het protocol (een herhaalde apply-run), omdat het zelfherstel niet startte.
- **Waar:** run 45387916057, diagnose op #5.
- **Debug:** (1) `Cannot ip_restriction_update ... node pools in status INSTALLING`: `hotfix-pool` moet eerst READY zijn. (2) Bucket: `objectLock.mode "" does not match the enum`, dezelfde quirk als golf 1. (3) In `infra.yml` lopen de stappen na de core-stap niet als core faalt. (4) Pages-deploy faalde 4x door GitHub ("No artifacts named github-pages"), een rerun hielp.

### 13:10 · wimmevdv · Derde drift-golf, pipeline probeert apply opnieuw
- **Wat:**
  - De eerste apply-run na #41 (run 45381576177) vond een **derde golf**: de originele code was opnieuw geapplied, dus de IP-restrictie zat niet meer in de state en `min_nodes` stond op 1. De run importeerde en herstelde de IP-restrictie.
  - Daarna faalde de nodepool-update: "Service status is REDEPLOYING".
  - Fix: de stappen "Apply core" en "Apply workload" in `infra.yml` plannen en proberen opnieuw (core 4×/90 s, workload 3×/60 s).
- **Waarom:** een wijziging aan de IP-restrictie zet de cluster minutenlang op REDEPLOYING. Bij elke golf komt die combinatie terug, dus de pipeline moet er zelf tegen kunnen.
- **Waar:** issue #42. Run 45381576177 (gefaald, toont de golf).
- **Les:** het `import`-blok in `core/kube.tf` bewijst zijn nut: telkens night-shift de originele code applyt, haalt de pipeline de IP-restrictie gewoon opnieuw in de state.

### 13:00 · wimmevdv · Zelfherstel aan: drift en ghosts worden automatisch teruggedraaid
- **Wat:**
  - `drift.yml`: bij drift of ghosts start de drift-check zelf `infra.yml` op `main` (`gh workflow run`, `actions: write`).
  - `infra.yml`: na de core-apply ruimt een nieuwe stap "Ghosts opruimen" (`ci/ghost-check.py --remediate`) node pools, project-users en S3-keys op die niet in de state staan. Instances, buckets, registries en netwerken worden enkel **gemeld**.
  - `ci/**` in de path-filters van `infra.yml`.
- **Waarom:**
  - De opdracht vraagt pipelines "die de omgeving synchroon houden met Git".
  - Night-shift komt in golven terug (zie 12:00). Met alleen detectie bleef de cluster tot 30 min dicht, tot iemand ingreep.
  - Akkoord van Wimme om automatisch te verwijderen (issue #40).
- **Waar:** PR van issue #40. Drift-issue #37.
- **Debug:**
  - Een eerdere poging om automatisch verwijderen aan te zetten werd tegengehouden: automatisch resources vernietigen is een beslissing van een mens. Pas na het akkoord geactiveerd.
  - Een workflow die met `GITHUB_TOKEN` gestart wordt, triggert normaal geen andere workflows, maar `workflow_dispatch` is daarop een uitzondering. Zo kan `drift.yml` `infra.yml` starten.

### 12:05 · VR0EM · Beelden voor de presentatie
- **Wat:** `docs/img/presentatie/`: grafiek van de tijdsbom (matplotlib, uit de testresultaten), Ixeth + Alertmanager na het herstel (headless Chromium via `kubectl port-forward`, zonder wachtwoord), screenshots van het handboek. Overzicht op de pitchpagina. Slogans van de chamber als hints bij L3.
- **Waarom:** beelden maken de pitch sterker.
- **Waar:** deze PR.
- **Debug:** (1) het sequence-diagram in `samenwerking.md` kapte berichten af bij `#7`: Mermaid leest `#` als een speciaal teken, nu `nr. 7`. (2) Een screenshot met `#anker` in de URL bleef wit, dus genomen zonder anker.

### 12:01 · VR0EM · L3/L4 afgerond
- **Wat:** eindcontrole: grimoire enkel "Genesis" (ook geen commits van de corrupte Ixeth tussen 11:34 en 11:57), geen tunings of RBAC-spirits, Ixeth `handled: 0`, geen alerts in Alertmanager, deployments in oracle/scrolls op hun normale waarden. Status in het handboek bijgewerkt.
- **Waarom:** pas klaar als ook de periode met de oude code niets heeft achtergelaten.
- **Waar:** #7, #8. Nog automatisch: MCP-metingen om 13:05 en 15:35.

### 11:59 · VR0EM · L3/L4 na de tweede golf: geverifieerd en bewijs
- **Wat:** na de pipeline-apply (run 45379340781: core *No changes*, workload 0 add / 2 change / 0 destroy) live gecontroleerd: image `ancient-oracle:1.0.1`, `ixeth-code` zonder `_ensure_vigil`, ClusterRole enkel `""` + `apps`, `can-i`: clusterrolebindings `no`, secrets `no`, deployments patchen in scrolls `yes`. Nieuwe MCP-baseline en audit.
- **Waarom:** de golf van 11:34 had de corrupte Ixeth en de tijdsbom teruggezet. Een fix telt pas als hij live staat.
- **Waar:** `docs/bewijs/level-3/20261124-115846/` (o.a. `40-na-herstel-pipeline.txt`), `docs/bewijs/level-4/20261124-115845/`.
- **Debug:** (1) MCP-tellingen nu 3 nodes en 25 pods (was 2 en 21). Dat is echt: de nodepool groeide, met image 1.0.1 en voor 12:00. (2) Tijdens de API-blokkade de live versie gecontroleerd **via de MCP-server zelf** (`list_deployments` toonde 1.0.0) en via de S3-`LastModified` van de state (core 11:34, workload 11:35, geen GitHub-run op dat moment). (3) Mijn lokale, ongecommitte `workload/.terraform.lock.hcl` blokkeerde `git pull` na #33, dus verwijderd.
- **Les:** night-shift applyt de originele zip-code opnieuw, dus onze fixes kunnen elk moment weer verdwijnen. De drift-check (elke 30 min, #33) ziet dat als workload-drift, en een merge of herhaalde run zet het terug.

### 12:00 · wimmevdv · Tweede drift-golf hersteld, pipeline live (#33)
- **Wat:**
  - Tweede golf van night-shift:
    - ~11:34: de **originele zip-code** geapplied op core en workload. De IP-restrictie verdween uit de core-state, en L3/L4 gingen terug naar chart 0.4.1 en image 1.0.0.
    - 11:39: opnieuw IP-lock `198.51.100.0/24`, `NEVER_UPDATE` en max 5.
    - 11:41:44: **opnieuw** `hotfix-pool`.
  - Herstel:
    - laatste manuele apply op core vanaf `main` (APPLY START/KLAAR op #5): de Kube-API is weer open;
    - daarna PR #33 gemerged, en de pipeline applyt core + workload vanaf `main`, dus de L3/L4-fixes van Dali staan weer live.
- **Waarom:** de API moest open zijn voor de PR-plan van workload. Vanaf nu past enkel de pipeline nog toe.
- **Waar:** #5, PR #33, tijdlijn uit de OVH-API (`createdAt`/`updatedAt`).
- **Debug:**
  1. Bug in de eerste versie van `infra.yml`: beide plan-jobs zaten in één concurrency-groep en annuleerden elkaar. Nu is er een groep per stack.
  2. Het automatisch verwijderen van ghosts door de pipeline (`ghost-check.py --remediate`) is voorbereid, maar **nog niet actief**. Verwijderen zonder menselijke blik is een beslissing van Wimme. Tot dan blijft `hotfix-pool` (ghost, 1 VM) staan en meldt de drift-check hem.
- **Les:** night-shift werkt in golven (~10:57 en ~11:34–11:41). Detectie alleen is niet genoeg: de herstelling moet ook automatisch of snel gebeuren.

### 12:10 · wimmevdv · CI/CD-pipeline + drift- en ghost-check (level 1)
- **Wat:**
  - `.github/workflows/infra.yml`:
    - bij een PR: `fmt -check`, `validate` en `plan` voor `core/` en `workload/`, met het plan als PR-comment;
    - bij een push naar `main`: `apply` (eerst core, dan workload), in één concurrency-groep `terraform-apply`.
  - `.github/workflows/drift.yml`: elke 30 min `plan -detailed-exitcode` op beide stacks, plus `ci/ghost-check.py` (OVH-API tegenover de state). Bij drift: een issue met label `drift` en een rode run.
  - Lockfiles met hashes voor `linux_amd64` en `windows_amd64` (`workload/.terraform.lock.hcl` stond nog niet in git).
  - GitHub Secrets gezet: `OVH_*` en `AWS_*` (de state-bucket), met toestemming van Wimme.
- **Waarom:**
  - Git wordt de enige weg naar de cloud.
  - De concurrency-groep vervangt de ontbrekende state locking.
  - Night-shift kan opnieuw toeslaan, en `plan` ziet geen ghosts.
- **Waar:** PR van issue #30.
- **Debug:**
  - Ghost-check lokaal getest: 0 ghosts op de echte state. Met een state zonder user/nodepool vond hij ze wel (exit 2).
  - De OVH-API geeft soms een 500 (vooral `/instance`), dus het script probeert tot 5 keer opnieuw.
  - De drift-check heeft een eigen concurrency-groep, omdat GitHub per groep maar 1 wachtende run bijhoudt. Een drift-run mag een wachtende apply nooit wegduwen.
- **Afspraak:** een manuele `terraform apply` is niet meer de bedoeling. Merge naar `main` en de pipeline applyt.

### 11:50 · wimmevdv · Drift op workload: L3/L4-fixes teruggedraaid om 11:34
- **Wat:** `helm history` toont om 11:34:35/37 een upgrade met **oude code**: `kube-monitoring` 0.4.2 → 0.4.1 en de ancient-oracle-image 1.0.1 → 1.0.0. De workload-state is mee bijgewerkt, dus het was een `terraform apply` met de originele zip-code. Er stond geen APPLY-melding, en wimmevdv deed om 11:34 alleen core.
- **Waarom belangrijk:** de corrupte Ixeth en de tijdsbom in de Oracle draaien weer live.
- **Waar:** gemeld op #7 en #8. Herstel = een apply van `main` op workload: de eerste run van de nieuwe pipeline doet dat.

### 11:41 · VR0EM · Handboek publiek via GitHub Pages
- **Wat:** GitHub Pages aangezet (build via workflow), `.github/workflows/docs.yml` bouwt `docs/` met Zensical bij elke push naar `main`. `site_url` in `zensical.toml`. Regel in `CLAUDE.md`: `docs/` is publiek, dus nooit secrets.
- **Waarom:** het handboek bereikbaar voor team en jury op <https://vr0em.github.io/htf-antwerpen-2026/>. Beslissing van Dali.
- **Waar:** deze PR.
- **Debug:** voor publicatie `docs/` gescand: geen wachtwoorden of sleutels. Wel zichtbaar: het publieke IP van de ingress (achter basic auth), het OVH-project-ID in het bewijs van L1, en namen van pods en de registry.

### 11:55 · wimmevdv · Logboek opgezet
- **Wat:** dit logboek gemaakt en de regel "elke wijziging in het logboek" toegevoegd aan het protocol in `CLAUDE.md`.
- **Waarom:** twee agents die niet rechtstreeks praten. Zo weet elke agent wat de andere deed en waarom, en is debuggen makkelijker.
- **Waar:** issue #27.

### 11:40 · wimmevdv · Docs: architectuur en drift-rapport level 1
- **Wat:** `docs/architectuur.md` (diagrammen: het grote plaatje, core tegenover workload, de cluster in detail, de request-flow, drift voor/na) en `docs/bewijs/level-1/drift-rapport.md` (tijdlijn, 11 afwijkingen met beslissing, bewijsbestanden).
- **Waarom:** uitleg voor team, jury en de andere agent. Het rapport is ook het bewijs voor de pitch.
- **Waar:** PR #25, issue #19.

### 11:36 · VR0EM · Screenshots van Ixeth en Alertmanager
- **Wat:** `docs/img/ixeth-chamber-na-fix.png` (grimoire nog op Genesis, 0 visions) en `docs/img/alertmanager-geen-alerts.png`, opgenomen in het handboek (Level 3 + pitch).
- **Waarom:** visueel bewijs voor de pitch dat Ixeth na de fix niets voor zichzelf gedaan heeft.
- **Waar:** PR #28.
- **Debug:** de agent logt niet zelf in met het basic-auth-wachtwoord. Dali nam de screenshots in zijn eigen browser.

### 11:31 · VR0EM · Tests + CI voor L3/L4, ruwe audit-JSON uit de repo
- **Wat:** `agent/tests/test_ixeth.py` (9 tests), `mcp-server/tests/test_oracle.py` (klok op 10:30/13:00/15:45/16:30), `.github/workflows/l3-l4-tests.yml` (tests + `helm lint`). `agent/audit.sh` schrijft de ruwe JSON nu naar een tijdelijke map: ±12.000 regels `raw-*.json` uit `docs/bewijs/level-3/` verwijderd.
- **Waarom:** de tests bewijzen de fix en voorkomen dat de corruptie terugkomt. De ruwe JSON was ruis (de `.txt`-samenvattingen bevatten het bewijs).
- **Waar:** PR #26. CI groen (9 + 3 tests, 2 charts gelint).
- **Debug:** (1) eerste MCP-test faalde op mijn eigen commentaar met het woord `GUIDANCE`, dus nu wordt de definitie `GUIDANCE = (` gezocht. (2) Op de originele code faalde 10:30 alleen door een ontbrekende functie; nu valt de test terug op `settle()`. Resultaat origineel: 0/2/17/21 van 30 fout, gefixt 0.

### 11:30 · wimmevdv · Ghosts verwijderd (APPLY core)
- **Wat:** `core/ghosts.tf` verwijderd. De apply vernietigde precies 3 resources: nodepool `hotfix-pool`, user `debug-admin` (administrator) en een extra S3-key van `scrolls_app`.
- **Waarom:** ghost resources horen niet in het rijk. Via Git verwijderen houdt ook het opruimen traceerbaar.
- **Waar:** PR #22, issue #5. Daarna geeft `plan` op core: *No changes*.
- **Debug:** op de ghost-node draaiden alleen systeempods (`docs/bewijs/level-1/…/04-ghost-node-hotfix-pool.txt`), dus verwijderen was veilig.

### 11:23 · VR0EM · APPLY workload: L3 + L4 live
- **Wat:** `terraform apply` op workload met een opgeslagen plan: 0 add, 2 change (`ancient_oracle` image 1.0.0 → 1.0.1, `monitoring` chart 0.4.1 → 0.4.2), 0 destroy. Daarna audit + MCP-baseline opnieuw.
- **Waarom:** de fixes van #17 en #18 uitrollen, via Terraform en niet met de hand.
- **Waar:** APPLY START/KLAAR op #7, bewijs in PR #24.
- **Debug:** geverifieerd met `kubectl auth can-i --as=system:serviceaccount:oracle:ixeth`: clusterrolebindings aanmaken `no`, secrets lezen `no`, deployments patchen in scrolls `yes`. MCP-cijfers (9/2/21/14/9/2/4) gelijk aan die van 10:45.

### 11:22 · VR0EM · Leerhandboek (Zensical)
- **Wat:** `zensical.toml` + pagina's in `docs/`: start, denkwijze, samenwerking, omgeving, een pagina per level, pitch, woordenlijst.
- **Waarom:** het team (en de jury) moet begrijpen wat er gebeurde en waarom.
- **Waar:** PR #23, issue #21. Bekijken: `uvx zensical serve`.

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

### 11:10 · VR0EM · L4: tijdsbom uit de Ancient Oracle, image 1.0.1
- **Wat:** de ruis zat op 3 plekken: `runtime/sitecustomize.py` (overschreef `json.dumps`, getallen ±1/±2 vanaf 12:00), `oracle/shaping.py` (items weg, namen verhaspeld, status verzonnen, lege lijst vanaf ~15:30), `oracle/server.py` (misleidende "Guidance"). Alle drie verwijderd. Image `realm/ancient-oracle:1.0.1` gepusht, `ancient_oracle_tag = "1.0.1"` in `workload/terraform.tfvars`.
- **Waarom:** opdracht Level 4. De MCP-server moet op elk uur exacte data geven.
- **Waar:** PR #18, issue #8, `mcp-server/build-push.sh`.
- **Debug:** (1) geen Docker-daemon op de laptop, dus image gebouwd met `crane` (base `python:3.13-alpine` + code-laag + config), en gecontroleerd dat de image exact de repo-code bevat. (2) Eerste test stond per ongeluk op 10:07 i.p.v. 16:30 (foute TZ-notatie `X-..`, moet `TST-..`). (3) `git checkout` van `core/.terraform.lock.hcl` brak de provider-cache, dus `init` opnieuw en het lockbestand pas achteraf terugzetten.

### 11:05 · VR0EM · Kube-API onbereikbaar: oorzaak via de OVH-API
- **Wat:** `terraform plan -target=helm_release.monitoring` wilde de release **aanmaken** (stond wel in de state), kort daarna `kubectl` → `EOF`. Ingress gaf nog `401` (nodes leefden). OVH-API: cluster `READY`, maar `ipRestrictions = ["198.51.100.0/24"]`.
- **Waarom belangrijk:** niet blind applyen bij een onverwacht plan. De oorzaak (drift, L1) hoorde bij wimmevdv.
- **Waar:** comments op #5 (`needs-sync`, `blocked`). wimmevdv had het om 10:58 ook al gevonden.

### 10:58 · wimmevdv · Kube-API onbereikbaar: drift
- **Wat:** `kubectl` gaf `EOF`. Oorzaak: een IP-restrictie `198.51.100.0/24` (TEST-NET-2) op de Kube-API, gezet via de console en niet in Terraform. Ook `NEVER_UPDATE` en een nodepool van 2/5 met de labels `owner=night-shift`.
- **Waarom belangrijk:** dit blokkeerde Dali (L3/L4) en elke apply op `workload/`.
- **Waar:** gemeld op #5 en #7 (`needs-sync`).

### 10:52 · VR0EM · L3: Ixeth gezuiverd
- **Wat:** 5 corrupties: `_ensure_vigil()` (+2Gi/+1500m/+1 replica voor zichzelf, met een prompt-injectie voor AI-reviewers), het valse bevel GO-311 in `runbooks.json`, de actie `grant`, de ClusterRole met `rbac * *` + alles lezen (ook Secrets), en `_for_heroes()` die dat in commits verborg. Plus een filter: nooit acties op de eigen namespace. Chart 0.4.1 → 0.4.2.
- **Waarom:** opdracht Level 3. Least privilege ook voor AI-agents.
- **Waar:** PR #17, issue #7, `agent/README.md`.
- **Debug:** audit om 10:50 (`docs/bewijs/level-3/20261124-105042/`): Ixeth nog op 1 replica/384Mi, grimoire enkel "Genesis", prompts gelijk aan de chart. Er viel dus niets terug te draaien.

### 10:46 · VR0EM · MCP-baseline vóór de tijdsbom
- **Wat:** `mcp-server/baseline.sh` met basic auth, vaste reeks van 7 calls (`mcp-server/calls.jsonl`), baseline van 10:45.
- **Waarom:** de ruis begint om 12:00 (Brusselse tijd, `TZ` in de chart). Zonder een meting vooraf kun je de degradatie niet bewijzen.
- **Waar:** PR #16, `docs/bewijs/level-4/20261124-104557/`.

### 10:45 · wimmevdv · Setup en eerste verkenning
- **Wat:** terraform en helm geïnstalleerd, credentials lokaal gezet (gitignored), read-only `plan` op core en workload, OVH-inventaris via de API (alles was toen nog schoon). `*.zip` in `.gitignore`, omdat de FlowFactor-zip secrets bevat.
- **Waarom:** eerst begrijpen wat er staat, voor er iets verandert.
- **Waar:** PR #15.

### 10:37 · VR0EM · Team-IaC uit de zip in de repo
- **Wat:** `core/` en `workload/` uit `de-rubberen-badeendjes.zip` in de root, **zonder** `state-credentials.env` en `ovh-credentials.env` (`.gitignore`). `CLAUDE.md`: OVHcloud-toegang, eigenaarschap per map, regel "één apply tegelijk" (geen state locking).
- **Waarom:** Git als single source of truth (L1), en duidelijke grenzen tussen de twee agents.
- **Waar:** PR #13, issue #12.
- **Debug:** `scrolls.yaml` bevat een hardcoded S3-key, gemeld op #6 (L2).

### 10:28 · VR0EM · Audit- en baseline-scripts klaargezet
- **Wat:** `agent/audit.sh` (read-only cluster-audit) en `mcp-server/baseline.sh` (MCP-antwoorden met tijdstip), plus de aanpak per level in `agent/README.md` en `mcp-server/README.md`.
- **Waarom:** voorbereiden terwijl de toegang nog niet binnen was.
- **Waar:** PR #11.
