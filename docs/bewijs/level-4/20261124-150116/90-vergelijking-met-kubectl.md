# Level 4: MCP-antwoorden (15:01) tegenover kubectl, zelfde moment

| Call | MCP | kubectl | Namen gelijk | Extra tekst (Guidance) |
|---|---|---|---|---|
| list_namespaces (alle) | 9 | 9 | ja | nee |
| list_nodes (alle) | 2 | 2 | ja | nee |
| list_pods (alle) | 22 | 21 | verschil: ancient-oracle-canary-1730 | nee |
| list_deployments (alle) | 14 | 14 | ja | nee |
| list_services (alle) | 9 | 9 | ja | nee |
| list_pods scrolls | 2 | 2 | ja | nee |
| list_deployments oracle | 4 | 4 | ja | nee |

Pod-fases buiten Running/Pending/Succeeded: 0

Resultaat: alles exact (enkel kortlevende canary-pods kunnen verschillen)

## Canary-pods (15:00, niet van ons)

Om 14:00Z (15:00) startte iets in `ancient` drie kortlevende pods met **onze image 1.0.1**:
`ancient-oracle-canary-1030`, `-1430` en `-1730`, elk ±12 s. De namen zijn de uren 10:30, 14:30 en 17:30:
vermoedelijk de controle van de organisatoren, die onze Oracle met een vervalste klok draait (zoals onze
eigen tests in `mcp-server/tests/`). Daarom staat er in `list_pods` één pod meer dan in kubectl een fractie later.
