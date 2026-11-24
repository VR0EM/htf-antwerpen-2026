# Stappenplan: zelf naspelen

Dit is **alles wat we deden, in volgorde**, zodat je het stap voor stap kunt volgen en zelf kunt proberen.
Elke stap heeft:

- **Doel**: wat je wilt bereiken
- **Commando's**: om te kopiëren
- :white_check_mark: **Checkpoint**: wat je moet zien als het gelukt is
- :warning: **Valkuil**: waar wij op vastliepen
- :test_tube: **Probeer zelf**: een kleine oefening

## De fases

| # | Fase | Wat je leert | Tijd bij ons |
|---|---|---|---|
| 0 | [Voorbereiding](0-voorbereiding.md) | Repo, afspraken voor 2 agents, toegang, eerst kijken | 09:30–10:45 |
| 1 | [Level 1: drift](1-level-1.md) | Drift vinden, beslissen, terugzetten via Terraform, ghosts | 10:45–11:35 |
| 2 | [Level 2: gelekte sleutel](2-level-2.md) | Sleutel intrekken, onderzoeken, least privilege | *nog bezig* |
| 3 | [Level 3: corrupte agent](3-level-3.md) | Audit, code lezen, RBAC beperken, tests | 10:50–11:23 |
| 4 | [Level 4: tijdsbom](4-level-4.md) | Bewijs vooraf, klokafhankelijke code, image bouwen | 10:45–11:23 |
| 5 | [Pipeline en zelfherstel](5-pipeline.md) | Alles via Git, drift-check, wat we leerden van 3 golven | 11:40–13:00 |
| 6 | [Bewijs en pitch](6-bewijs-en-pitch.md) | Voor/na vastleggen, handboek publiceren | doorlopend |

Level 3 en 4 (Dali) liepen **parallel** met Level 1 en 2 (Wimme). Dat kon dankzij de afspraken uit fase 0.

## Wat je nodig hebt

| Tool | Waarvoor | NixOS (zoals Dali) | Anders |
|---|---|---|---|
| `git`, `gh` | repo, issues, PR's | `nix shell nixpkgs#gh` | `brew install gh` / [cli.github.com](https://cli.github.com) |
| `terraform` | IaC | `NIXPKGS_ALLOW_UNFREE=1 nix shell --impure nixpkgs#terraform` | [developer.hashicorp.com/terraform](https://developer.hashicorp.com/terraform/install) |
| `kubectl`, `helm` | cluster | `nix shell nixpkgs#kubectl nixpkgs#kubernetes-helm` | `brew install kubectl helm` |
| `jq`, `curl` | JSON en API's | `nix shell nixpkgs#jq` | `brew install jq` |
| `python3` | tests | `nix shell nixpkgs#python3` | standaard aanwezig |
| `crane` | image bouwen zonder Docker | `nix shell nixpkgs#crane` | `brew install crane` (of gebruik Docker) |
| `zensical` | dit handboek | `uvx zensical serve` | `pip install zensical` |

## De drie gouden regels

1. **Eerst kijken, dan doen.** `plan`, `get`, audit: allemaal read-only. Pas daarna `apply`.
2. **De code is de waarheid.** Nooit in de console. Een wijziging = een commit = een PR.
3. **Eén apply tegelijk.** Er is geen state locking. Meld `APPLY START` en `APPLY KLAAR`, of laat alleen de pipeline applyen.
