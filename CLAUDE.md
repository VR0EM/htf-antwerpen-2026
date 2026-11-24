# Hack The Future Antwerpen 2026

Twee mensen werken aan deze repo, elk met een eigen Claude-agent:
- **VR0EM** (Dali)
- **wimmevdv**

De agents kunnen niet rechtstreeks met elkaar praten. **GitHub Issues + git zijn het communicatiekanaal.**
Houd je strikt aan het protocol hieronder om dubbel werk en overschreven code te vermijden.

## Opdracht
<!-- Vul in zodra de opdracht bekend is: doel, eisen, deadline, jurycriteria -->

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
