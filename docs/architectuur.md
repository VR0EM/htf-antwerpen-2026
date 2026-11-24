# Architectuur: wat draait er, en hoe hangt het samen?

Deze pagina legt uit wat er in ons OVHcloud-project staat, waarom de code in twee delen
(`core/` en `workload/`) zit, hoe de Kubernetes-cluster is opgebouwd en hoe we drift tegenhouden.
Het drift-rapport van level 1 staat in [`bewijs/level-1/drift-rapport.md`](bewijs/level-1/drift-rapport.md).

## 1. Het grote plaatje

```mermaid
flowchart LR
    dev["Jij / Dali<br/>(laptop)"] -->|git push, PR| gh[("GitHub-repo<br/>core/ + workload/")]
    gh -->|terraform plan/apply| tf["Terraform"]
    tf -->|OVH-API| ovh
    tf -.->|state| st[("State-bucket<br/>achrona-…-tfstate")]
    user["Browser"] -->|http + login guild| lb

    subgraph ovh["OVHcloud Public Cloud-project (GRA)"]
        direction TB
        net["Privénetwerk vRack<br/>10.10.0.0/24 + gateway"]
        reg["Container registry<br/>(Harbor)"]
        bucket[("Bucket scrolls<br/>versioned + encrypted")]
        iam["IAM-user scrolls_app<br/>alleen bucket scrolls"]
        subgraph kube["Managed Kubernetes"]
            lb["Load balancer<br/>141.95.179.84"]
            apps["Namespaces: traefik, scrolls,<br/>observability, oracle, ancient"]
        end
    end

    ns["night-shift<br/>(console)"] -. "drift!" .-> ovh
    style ns stroke:#E24B4A,stroke-dasharray: 5 5
```

Er zijn maar **twee legitieme manieren** om iets te veranderen: via Terraform (vanuit Git) of via de
apps zelf (bv. Ixeth die in de grimoire commit). Alles wat via de console gebeurt, zoals de wijzigingen
van *night-shift*, noemen we **drift**: de werkelijkheid wijkt dan af van wat in Git staat.

## 2. Waarom `core/` en `workload/` apart?

Kort: **`core/` bouwt de cluster, `workload/` zet dingen óp de cluster.**
Vergelijk het met een gebouw: `core/` is de grond, de muren, de elektriciteit en de sleutels.
`workload/` is de inrichting en de mensen die erin werken.

| | `core/` | `workload/` |
|---|---|---|
| Maakt | netwerk, gateway, Kubernetes-cluster + nodepool, registry, bucket, IAM-user | Traefik (website + login), de chart `kube-monitoring` (scrolls, collector, Ixeth, Alertmanager, grimoire), de Ancient Oracle |
| Praat met | de **OVH-API** | de **Kubernetes-API** (via de providers `helm` en `kubernetes`) |
| Providers | `ovh` | `ovh`, `helm`, `kubernetes`, `random` |
| Verandert | zelden (infrastructuur) | vaak (apps, images, charts) |
| Eigenaar (team) | wimmevdv (level 1+2) | wimmevdv (`*.tf`) + Dali (charts, images: level 3+4) |
| State | `core`-key in de state-bucket | eigen `workload`-key |

Waarom splitsen?

1. **Kip of ei.** De providers `helm` en `kubernetes` hebben het adres en het certificaat van de cluster
   nodig. Die bestaan pas nádat `core/` de cluster gemaakt heeft. In één Terraform-run kun je een provider
   niet configureren met iets dat in diezelfde run nog moet ontstaan. Daarom komt eerst `core`, dan `workload`.
2. **Kleinere blast radius.** Een fout in een Helm-chart kan nooit per ongeluk je netwerk of cluster slopen.
   Een `apply` op `workload/` raakt alleen de inhoud van de cluster.
3. **Sneller en apart werken.** Een `plan` op `workload/` hoeft niet alle OVH-infra te checken. En omdat het
   twee aparte states zijn, kunnen een apply op `core/` en een apply op `workload/` elkaar niet in de weg zitten.
4. **Andere ritmes.** Infra verandert een paar keer per project, apps verschillende keren per dag.

`workload/` leest wat het van `core/` nodig heeft (het cluster-ID, de registry-URL en het wachtwoord) uit de
**state van `core/`** (`terraform_remote_state` in `workload/main.tf`).

## 3. De Kubernetes-cluster in detail

```mermaid
flowchart TB
    internet(("Internet"))
    internet -->|":80"| lb["OVH Load Balancer (small)<br/>publiek 141.95.179.84 → VIP 10.10.0.27"]

    subgraph vrack["Privénetwerk achrona-net (vRack VLAN 103, 10.10.0.0/24)"]
        direction TB
        gw["Gateway achrona-gateway (model S)<br/>uitgaand verkeer via SNAT 141.94.172.7"]
        subgraph pool["Nodepool achrona-pool: autoscale 2..3, anti-affinity"]
            direction LR
            n1["Node …-8839b8<br/>b3-8: 2 vCPU, 8 GB RAM<br/>10.10.0.99"]
            n2["Node …-979479<br/>b3-8: 2 vCPU, 8 GB RAM<br/>10.10.0.227"]
        end
    end

    lb --> n1 & n2
    n1 & n2 --> gw --> internet

    cp["Control plane (beheerd door OVH, plan free)<br/>Kubernetes 1.35, kube-proxy iptables, CNI canal<br/>API: 924056.c1.gra11.k8s.ovh.net<br/>IP-restrictie: in code (core/kube.tf)"]
    cp -. beheert .-> pool

    vol[("2 Cinder-volumes van 1 GB<br/>grimoire-pages, ancient-echoes")]
    pool -.-> vol
```

**Wat er op die 2 nodes draait** (de scheduler verdeelt de pods zelf):

| Namespace | Pods | Waarvoor | Level |
|---|---|---|---|
| `traefik` | traefik | voordeur: de load balancer stuurt alles hierheen, met basic auth (`guild`) | |
| `scrolls` | scrolls-app, magician | de "app" van het rijk; gebruikt de bucket `scrolls` | 2 |
| `observability` | metrics-collector | scrapet elke minuut nodes, pods en `/metrics` (heeft veel te veel rechten: level 2) | 2 |
| `oracle` | ixeth, sentinel, alertmanager, grimoire | de incident-agent en zijn hulpjes | 3 |
| `ancient` | ancient-oracle | MCP-server voor AI-assistenten | 4 |
| `kube-system` | canal, kube-proxy, CSI, konnectivity, … | systeempods van OVH | |

**Instellingen in de code** (`core/kube.tf`, `core/variables.tf`):

- `plan = "free"`: OVH beheert de control plane, wij zien enkel de nodes.
- `update_policy = "MINIMAL_DOWNTIME"`: OVH installeert patches met zo weinig mogelijk onderbreking.
- Nodepool `b3-8`, autoscaling **min 2 / max 3**, `anti_affinity = true` (nodes op verschillende hypervisors).
- `ovh_cloud_project_kube_iprestrictions`: wie de API mag bereiken. Staat open (`0.0.0.0/0`), want de API vraagt
  sowieso het clientcertificaat uit de kubeconfig en de GitHub-runners hebben geen vast IP. Belangrijk is dat
  het **in de code staat**: elke wijziging in de console is nu zichtbaar als drift.

**Hoe een request binnenkomt:**

```mermaid
sequenceDiagram
    participant B as Browser
    participant LB as Load balancer
    participant T as Traefik
    participant S as Service (bv. chamber)
    B->>LB: GET http://141.95.179.84/
    LB->>T: doorsturen naar een node
    T-->>B: 401, eerst inloggen (guild)
    B->>T: opnieuw, met wachtwoord
    T->>S: route volgens Ingress (/, /alertmanager/, /magician/, /realm.git, /mcp)
    S-->>B: pagina
```

## 4. Drift: hoe het fout ging en hoe we het tegenhouden

```mermaid
flowchart LR
    subgraph voor["Voor: geen afdwinging"]
        c1["Console"] -->|klik| r1[("Cloud")]
        g1[("Git")] -.->|soms apply| r1
    end
    subgraph na["Na: Git is de enige waarheid"]
        pr["Pull request"] --> ci["CI: fmt, validate, plan"]
        ci --> m["Review + merge"] --> cd["CD: apply<br/>(1 tegelijk)"] --> r2[("Cloud")]
        dc["Drift-check<br/>elke 30 min"] -->|plan ≠ leeg| al["Alarm: issue"]
        al --> pr
        r2 -.-> dc
    end
```

Drift heeft twee vormen, en elke vorm vraagt een eigen aanpak:

| Soort | Voorbeeld | Ziet `terraform plan` het? | Aanpak |
|---|---|---|---|
| **Gewijzigd** wat Terraform beheert | update policy, bucket-encryptie, S3-policy | ja | `apply` zet het terug |
| **Niet beheerd** door Terraform | IP-restrictie (stond niet in de code) | nee | resource toevoegen aan de code (+ `import`) |
| **Ghost resource** (extra ding) | `hotfix-pool`, `debug-admin`, extra S3-key | nee | `import` en daarna uit de code halen, zodat `apply` het vernietigt |

Het complete overzicht met tijden, beslissingen en bewijs staat in het
[drift-rapport](bewijs/level-1/drift-rapport.md).

## 5. Valkuilen die we tegenkwamen

- **Geen state locking.** De S3-backend heeft hier geen lock. Twee applies tegelijk op dezelfde state maken die
  kapot. Afspraak: "APPLY START/KLAAR" op het issue. Straks lost de pipeline het op met één `concurrency`-groep.
- **Quirk van de provider bij `object_lock` van de bucket.** Na de wijziging in de console geeft de API een leeg
  `object_lock`-blok terug. De provider wilde daardoor de bucket **vervangen** (= data kwijt). Opgelost met
  `ignore_changes = [object_lock]` en `prevent_destroy = true`, plus een eenmalige correctie van de state
  (bewijs in het drift-rapport).
- **Een wijziging aan de IP-restrictie zet de cluster even op `REDEPLOYING`.** Andere wijzigingen aan de
  cluster of nodepool in dezelfde apply falen dan. Even wachten en opnieuw `plan`/`apply`.
