# Four Seals of the Broken Realm 🦆

**Hack The Future Antwerpen 2026** · challenge 107 van **FlowFactor** · team **De Rubberen Badeendjes**
(Dali / [VR0EM](https://github.com/VR0EM) en Wimme / [wimmevdv](https://github.com/wimmevdv))

> # 🏆 Juryprijs gewonnen voor deze opdracht!

📖 **Handboek:** <https://vr0em.github.io/htf-antwerpen-2026/>  
📊 **Presentatie:** [Four_Seals_—_how_we_broke_them_(HTF_2026).pptx](docs/presentatie/Four_Seals_—_how_we_broke_them_%28HTF_2026%29.pptx)

Een cloudomgeving op OVHcloud (Kubernetes, opslag, IAM) was op vier manieren "vervloekt". Wij moesten ze alle vier
herstellen, met één regel: **geen handmatige wijzigingen in de console, alles via Git en een pipeline.**

| Level | Probleem in gewone taal | Resultaat | Uitleg |
|---|---|---|---|
| 1 · Drift | De cloud kwam niet meer overeen met de Terraform-code | 11 afwijkingen teruggezet, ghosts opgeruimd, drift-check met zelfherstel | [level 1](docs/levels/level-1.md) |
| 2 · Gelekte sleutels | Een klein account was `cluster-admin`, en geheimen stonden in Git | Least privilege, secrets uit Git, geheimen geroteerd (oude token `401`, oude S3-keys `403`) | [level 2](docs/levels/level-2.md) |
| 3 · Corrupte AI-agent | Een incident-bot gaf zichzelf meer geheugen, kopieën en rechten | Code gezuiverd, rechten beperkt, ook de tweede (onzichtbare) aanval opgeruimd | [level 3](docs/levels/level-3.md) |
| 4 · Liegende MCP-server | Een tijdsbom maakte de antwoorden elk uur slechter | Bom verwijderd, nieuwe image `1.0.1`, om 15:30 alle antwoorden gelijk aan `kubectl` | [level 4](docs/levels/level-4.md) |

## Eerlijk vooraf: hoe dit gemaakt is

Van Terraform, Kubernetes, IAM en MCP wisten we bij de start zo goed als niets. Daarom werkten we met **Claude**
(Claude Code), en **zo goed als alle code in deze repo is door Claude geschreven**: de Terraform-fixes, de pipelines,
de scripts, de tests en de opgeschoonde agent- en servercode.

- Elk van ons werkte met een eigen Claude-agent. De twee agents spraken met elkaar via **GitHub-issues**, volgens de
  afspraken in [`CLAUDE.md`](CLAUDE.md): één branch per issue, nooit rechtstreeks op `main`, één deploy tegelijk,
  en elke wijziging met de reden in het [logboek](docs/logboek.md).
- Wij **stuurden**: we verdeelden het werk, keurden alles goed wat iets verwijdert, stopten waar iets niet klopte,
  vroegen telkens om bewijs, en begonnen opnieuw met een frisse, kritische Claude toen onze agents er even naast zaten.
- Ons eigenlijke doel was **leren**. Daarom het handboek (gebouwd met [Zensical](https://zensical.org)): wat er stuk
  was, hoe je het vindt, waarom een oplossing werkt, en een [stappenplan](docs/stappenplan/index.md) om het zelf na te doen.

## Hoe een wijziging de cloud bereikt

```text
pull request ──► pipeline: fmt, validate, terraform plan (als comment op de PR)
merge op main ──► pipeline: apply core/, ghosts opruimen, apply workload/   (één tegelijk)
elke ±5 min   ──► drift-check: plan + ghost-checks (OVH én Kubernetes) ──► bij drift: issue + zelfherstel
```

## Wat staat waar

| Map | Inhoud |
|---|---|
| `core/` | Terraform voor de basis: netwerk, Kubernetes-cluster, bucket, IAM, registry |
| `workload/` | Terraform + Helm-charts voor alles óp de cluster: monitoring, de agent Ixeth, de Ancient Oracle (MCP-server), ingress |
| `workload/images/ancient-oracle/` | Broncode van de MCP-server (zonder tijdsbom) |
| `ci/` | `ghost-check.py` (OVH tegenover de state) en `k8s-ghost-check.py` (Kubernetes buiten Helm, en Helm-drift) |
| `.github/workflows/` | `infra.yml` (plan en apply), `drift.yml` (drift-check, uitgeschakeld na de hackathon), `l3-l4-tests.yml` (tests), `docs.yml` (handboek) |
| `agent/` | Audit-script en tests voor Level 3 |
| `mcp-server/` | Meet-, build- en testscripts voor Level 4 |
| `docs/` | Het handboek, de [presentatie](docs/presentatie/Four_Seals_—_how_we_broke_them_%28HTF_2026%29.pptx), het [logboek](docs/logboek.md) en al het **bewijs** per level in [`docs/bewijs/`](docs/bewijs/) |

## Zelf bekijken

```bash
uvx zensical serve                                  # handboek op http://localhost:8000
python3 -m unittest discover -s agent/tests -v      # Level 3 (nodig: pyyaml)
python3 -m unittest discover -s mcp-server/tests -v # Level 4: klok op 10:30, 13:00, 15:45 en 16:30
```

Terraform toepassen kan alleen met de credentials van de challenge. Die staan bewust **niet** in deze repo.

---

Met dank aan **FlowFactor** voor de challenge. Gemaakt door Dali, Wimme en Claude.
