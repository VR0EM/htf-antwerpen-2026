# Four Seals of the Broken Realm

**Hack The Future Antwerpen 2026**: challenge 107 van **FlowFactor**.
Team **de-rubberen-badeendjes**: VR0EM (Dali) en wimmevdv (Wimme), elk met een eigen Claude-agent.

Dit handboek legt uit **wat er stuk was**, **hoe we het vonden**, **hoe we het oplosten** en vooral
**hoe je zoiets zelf aanpakt**. Lees het van boven naar beneden. Geen voorkennis nodig.

!!! example "Zelf proberen?"
    Volg het [**stappenplan**](stappenplan/index.md): alles wat we deden, in volgorde, met commando's, checkpoints en valkuilen.

## Het verhaal in 30 seconden

Het rijk Achrona draait op een cloudomgeving (OVHcloud) met een Kubernetes-cluster.
Door *The Desync* klopt de werkelijkheid niet meer met wat er in de code staat.
Er zijn vier "zegels" (problemen) te herstellen:

| Level | Zegel | Probleem in gewone taal | Wie |
|---|---|---|---|
| 1 | Ancient Scrolls | Iemand heeft de cloud **met de hand** aangepast. De code en de werkelijkheid lopen uit elkaar (*drift*). | Wimme |
| 2 | Shadow | Een **sleutel is gelekt** en een account heeft veel te veel rechten. | Wimme |
| 3 | Oracle | Een **AI-agent** die incidenten oplost, is corrupt: hij geeft zichzelf stiekem meer resources en rechten. | Dali |
| 4 | Echo (bonus) | Een **MCP-server** (de "ogen" van een AI-assistent op de cluster) liegt steeds meer naarmate de dag vordert. | Dali |

!!! tip "De gouden regel van deze opdracht"
    **Geen handmatige wijzigingen in de console.** Alles verandert via **Git** (code) en daarna
    **Terraform** (dat de code uitvoert). Zo is de code altijd de waarheid.

## Hoe alles samenhangt

```mermaid
flowchart LR
    Git[("GitHub-repo<br/>= de waarheid")] -->|terraform apply| Core["core/<br/>cluster, netwerk,<br/>bucket, IAM, registry"]
    Git -->|terraform apply| Workload["workload/<br/>alles óp de cluster"]
    Workload --> Ixeth["Ixeth<br/>(incident-agent, L3)"]
    Workload --> Oracle["Ancient Oracle<br/>(MCP-server, L4)"]
    Workload --> Scrolls["scrolls-app<br/>(gebruikt de bucket, L2)"]
    Console(["Handmatig in de console<br/>(night-shift)"]) -.->|drift, L1| Core
```

## Status

Alle vier de levels zijn opgelost, via Git en de pipeline, en live gecontroleerd (eindstand 15:30).

| Level | Wat we deden | Bewijs |
|---|---|---|
| 1 | 11 afwijkingen teruggezet in de code, ghosts via Git opgeruimd, pipeline met drift-check en zelfherstel | `docs/bewijs/level-1/` |
| 2 | `cluster-admin` weg (least privilege), secrets uit Git, alle gelekte geheimen geroteerd: oude token `401`, oude S3-keys `403` | `docs/bewijs/level-2/` |
| 3 | 5 corrupties uit de code (10:52). Om 13:39 kwam een tweede, onzichtbare corruptie: ook die is gevonden en opgeruimd | `docs/bewijs/level-3/` |
| 4 | Tijdsbom op 3 plekken verwijderd, image `1.0.1`. Om 15:30 waren alle 7 MCP-antwoorden gelijk aan `kubectl` | `docs/bewijs/level-4/` |

Bewust uitgesteld: de kubeconfig resetten (stap 4/4 van de rotatie in Level 2). Bij OVH installeert dat alle nodes opnieuw, en dat deden we niet vlak voor de demo.

!!! info "Hoe dit gemaakt is"
    Zo goed als alle code, de tests en de pipelines zijn geschreven door **Claude** (Claude Code), als twee agents die
    via GitHub-issues samenwerkten. Wij stuurden, namen de beslissingen en controleerden het bewijs. Dit handboek is
    vooral ons leermateriaal: zo begrijpen we zelf wat er gebeurd is.

!!! note "Online: <https://vr0em.github.io/htf-antwerpen-2026/>"
    Lokaal bekijken:

    ```bash
    uvx zensical serve      # of: pip install zensical && zensical serve
    ```
    Open daarna <http://localhost:8000>.
