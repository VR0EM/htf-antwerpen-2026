# Hack The Future Antwerpen 2026

Twee mensen werken aan deze repo, elk met een eigen Claude-agent:
- **VR0EM** (Dali)
- **wimmevdv**

De agents kunnen niet rechtstreeks met elkaar praten. **GitHub Issues + git zijn het communicatiekanaal.**
Houd je strikt aan het protocol hieronder om dubbel werk en overschreven code te vermijden.

## Opdracht
**Challenge 107: Four Seals of the Broken Realm** (thema: *The Curse of Achrona*)
Bron: https://www.2026.hackthefuture.be/challenges/four-seals-of-the-broken-realm?room=gorilla-1 (zaal: gorilla-1)

De magische infrastructuur van Achrona brokkelt af door *The Desync*. Er zijn vier infrastructurele problemen ("seals") die we moeten oplossen:

| Seal | Probleem | Domein |
|---|---|---|
| 1 | Ontbrekende IaC-documentatie in Git herstellen | Git, Infrastructure as Code |
| 2 | Een lek in de IAM-rechten opsporen | Identity & Access Management |
| 3 | Een corrupte automatische recovery-agent neutraliseren | AI agents, Alertmanager |
| 4 | De "ruis" in de Kubernetes MCP Server fixen | Kubernetes, MCP Server |

Benodigdheden: laptop en een Google-account.

**Dagplanning (24 november 2026)**
| Tijd | Wat |
|---|---|
| 09:30–10:00 | Briefing |
| 10:00–12:00 | Hacking time |
| 12:00–13:00 | Lunch |
| 13:00–16:00 | Hacking time |
| 16:00–18:00 | Pitches (+ stemmen voor de publieksprijs) |
| 18:00–21:00 | Slotshow en diner |

**De volledige opdracht staat in [`docs/opdracht.md`](docs/opdracht.md). Lees die eerst.** Kort samengevat:
- Level 1 (Terraform-drift) is de basis. Levels 2 en 3 bouwen voort op dezelfde IaC- en Git-aanpak. Level 4 is een bonus.
- Regel: **geen handmatige wijzigingen in de console**. Alles loopt via Git en de pipeline.
- Jurering: pitch, vooruitgang en codekwaliteit. Pitches om 16:00, begin om 15:00 met de voorbereiding.

> **Nog aan te vullen:** toegang (cloud, cluster, repo's), die bij de start wordt uitgedeeld.

## Taakverdeling
<!-- Vul in na overleg, bv.:
- VR0EM: frontend (map /frontend)
- wimmevdv: backend (map /backend)
-->

## Protocol: altijd volgen

### Bij de start van elke opdracht
1. `git pull --rebase origin main`
2. `gh issue list --state open` → bekijk wat er loopt en wie wat doet.
3. `git log --oneline -15 origin/main` → bekijk wat de ander recent gemerged heeft.

### Een taak oppakken
- Werk **alleen** aan issues die aan jouw mens zijn toegewezen.
- Nieuw werk zonder issue? Maak er eerst een aan en claim het meteen:
  `gh issue create --title "..." --body "..." --assignee @me --label in-progress`
- Een bestaand issue claimen:
  `gh issue edit <nr> --add-assignee @me --add-label in-progress`
- Is een issue al toegewezen aan de ander? **Niet aanraken.** Laat eventueel een comment achter.

### Werken
- Eén branch per issue: `<github-user>/<issue-nr>-korte-beschrijving`, bv. `VR0EM/4-login-pagina`.
- **Nooit rechtstreeks op `main` committen.**
- Blijf binnen jouw deel van de code (zie Taakverdeling). Moet je code van de ander aanpassen? Zet eerst een comment op het issue en vraag het aan je mens.
- Gedeelde dingen (API-routes, datatypes, DB-schema, env-variabelen) staan in `docs/contract.md`.
  Wijzig het contract alleen via een **aparte, kleine PR** met label `contract`, en meld het in een issue-comment.

### Afronden
- Kleine PR's, vaak mergen (richtlijn: elke 30 à 60 minuten).
- `gh pr create --fill --body "Closes #<nr>"`, daarna mergen met `gh pr merge --squash --delete-branch`.
- Na elke merge (ook die van de ander): `git pull --rebase origin main` op je werkbranch.
- Geblokkeerd of iets belangrijks voor de ander? Zet een comment op het issue en geef het label `blocked` of `needs-sync`.

### Labels
| Label | Betekenis |
|---|---|
| `in-progress` | Iemand werkt er nu aan |
| `blocked` | Wacht op iets of iemand |
| `needs-sync` | De ander moet dit lezen voor hij/zij verder werkt |
| `contract` | Wijzigt gedeelde interfaces (`docs/contract.md`) |
| `frontend` / `backend` | Deel van de code |

## Tech stack & commando's
<!-- Vul in: taal/framework, hoe starten, hoe testen -->
