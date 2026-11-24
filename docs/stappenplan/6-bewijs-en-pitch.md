# Fase 6: Bewijs en pitch

## Stap 6.1: Bewijs verzamelen terwijl je werkt

| Moment | Wat | Waar |
|---|---|---|
| Vóór de fix | audit, baseline, plan, API-output | `docs/bewijs/<level>/<datum-uur>/` |
| Na de fix | dezelfde commando's opnieuw | idem, nieuwe map |
| Altijd | een entry in het logboek (wat, waarom, waar, debug) | `docs/logboek.md` |

:warning: **Valkuil:** ruwe dumps (we hadden ±12.000 regels JSON) zijn geen bewijs maar ruis. Bewaar de **leesbare samenvatting**.

:warning: **Valkuil:** `docs/` is publiek (GitHub Pages). **Nooit** wachtwoorden, sleutels of kubeconfigs erin.

## Stap 6.2: Screenshots zonder wachtwoord

```bash
kubectl port-forward -n oracle svc/ixeth 18080:80 &
kubectl port-forward -n oracle svc/alertmanager 19093:9093 &
chromium --headless=new --window-size=1280,720 --screenshot=ixeth.png http://localhost:18080/
```

## Stap 6.3: Dit handboek

```bash
uvx zensical serve            # lokaal, http://localhost:8000
```

Online: bij elke push naar `main` publiceert `.github/workflows/docs.yml` het naar
<https://vr0em.github.io/htf-antwerpen-2026/>.

:warning: **Valkuil:** de Pages-deploy faalde soms door GitHub zelf ("No artifacts named github-pages"). Een herstart van de run hielp.

## Stap 6.4: Pitch

Zie de [pitchpagina](../pitch.md): opbouw, sterke punten en beelden.
