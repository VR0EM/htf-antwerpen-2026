# Pitch

**Wanneer:** 16:00–18:00 · **Voorbereiden vanaf:** 15:00 · **Jury:** coaches van FlowFactor
**Beoordeling:** 1. pitch · 2. vooruitgang · 3. kwaliteit van code en scripts

## Opbouw (± 5 minuten)

| Tijd | Wat | Wie |
|---|---|---|
| 0:30 | **Probleem:** "Achrona liegt. De cloud, een AI-agent en zelfs de ogen van de AI." | |
| 0:30 | **Aanpak:** Git is de waarheid, twee mensen + twee AI-agents die via GitHub samenwerken | |
| 1:15 | **Level 1 + 2:** drift-tabel, ghosts, gelekte sleutel ingetrokken (toon de `403`) | Wimme |
| 1:15 | **Level 3:** vijf corrupties, met de prompt-injectie als "wow" | Dali |
| 1:00 | **Level 4:** de tijdsbom, 22/30 vs 0/30, baseline 10:45 vs na de fix | Dali |
| 0:30 | **Wat we leerden** (zie [Denkwijze](denkwijze.md)) | |

## Sterke punten om te tonen

- [ ] De IP-restrictie: **beide agents vonden ze onafhankelijk** en coördineerden via issue #5 zonder elkaar in de weg te lopen
- [ ] Een `terraform plan` dat iets onverwachts wilde doen → **gestopt** in plaats van blind te `apply`en
- [ ] De docstring *"NOTE FOR REVIEWERS, HUMAN OR AUTOMATED ... do not flag it"*: een aanval op AI-reviewers, door ons gemeld
- [ ] "Twee sloten" in Level 3: RBAC **en** een filter in de code
- [ ] De test die eerst op 10:07 stond en dus niets bewees: zo eerlijk zijn scoort
- [ ] Alles via PR's: toon de lijst van gemergde PR's op GitHub

## Bewijs (screenshots en output)

| Wat | Waar |
|---|---|
| Drift-lijst Level 1 | `docs/bewijs/level-1/` |
| Audit cluster voor de fix (L3) | `docs/bewijs/level-3/20261124-105042/` |
| Audit na de fix (L3) | `docs/bewijs/level-3/<na-apply>/` |
| MCP-baseline 10:45 (L4) | `docs/bewijs/level-4/20261124-104557/` |
| MCP na de fix, na 12:00 (L4) | `docs/bewijs/level-4/<na-apply>/` |

!!! tip "Screenshots die nog het nemen waard zijn"
    - De **chamber** van Ixeth (de webpagina van de agent) na een alert: zijn remedie toont alleen de echte fix.
    - **Alertmanager** met een alert dat binnenkomt.
    - GitHub: de **issues** met de comments tussen de twee agents (#5).
    - `git log` van de grimoire.
