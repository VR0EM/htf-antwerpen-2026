# Level 4: MCP-antwoorden (15:30) tegenover kubectl, zelfde moment

| Call | MCP | kubectl | Namen gelijk | Extra tekst (Guidance) |
|---|---|---|---|---|
| list_namespaces (alle) | 9 | 9 | ja | nee |
| list_nodes (alle) | 2 | 2 | ja | nee |
| list_pods (alle) | 21 | 21 | ja | nee |
| list_deployments (alle) | 14 | 14 | ja | nee |
| list_services (alle) | 9 | 9 | ja | nee |
| list_pods scrolls | 2 | 2 | ja | nee |
| list_deployments oracle | 4 | 4 | ja | nee |

Pod-fases buiten Running/Pending/Succeeded: 0

Resultaat: alles exact (enkel kortlevende canary-pods kunnen verschillen)

## Wat de originele code om 15:30 had gedaan

`shaping.pressure(15.5)` = smoothstep((15.5 − 12) / 4) ≈ **0.96**. Boven 0.9 gaf `settle()` voor elke lijst **`[]`**
terug, en `server.py` verving dat lege antwoord door twee willekeurige "Guidance"-zinnen. Elke lijst hierboven was
dus leeg of verzonnen geweest. Met image 1.0.1: exact wat de cluster zegt.
