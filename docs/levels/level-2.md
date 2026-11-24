# Level 2: Seal of the Shadow (gelekte sleutel)

**Eigenaar:** Wimme · **Issue:** #6

!!! success "Opgelost"
    Zie [Wat we deden](#wat-we-deden) onderaan. Bewijs: `docs/bewijs/level-2/`.

## De opdracht in gewone taal

Een sleutel van een service account is uitgelekt en dat account kan te veel. Maak de oude sleutel
**ongeldig**, maak een nieuwe die **veilig bewaard** wordt, zoek uit wat de aanvaller deed, en geef het
account enkel de rechten die het nodig heeft. Alles in code.

## Wat we eerst zagen

In `workload/charts/kube-monitoring/templates/scrolls.yaml` staat een **sleutel in platte tekst**:

```yaml
kind: Secret
metadata:
  name: scrolls-app-credentials
stringData:
  S3_ACCESS_KEY: 9d4e1c7a...   # (1)!
  S3_SECRET_KEY: f0a8c35e...
```

1. Een sleutel in een Git-repo is een **gelekte sleutel**: iedereen met leestoegang (nu of ooit) heeft hem.

Tegelijk maakt `core/iam.tf` al een nette, beperkte gebruiker `scrolls_app` aan, met een S3-sleutel
die **alleen** de bucket `scrolls` mag gebruiken. Die wordt alleen niet gebruikt.

In Level 1 bleek ook dat de policy van `scrolls_app` live op `s3:*` stond, en dat er een **extra S3-sleutel**
en een account `debug-admin` bestonden. Dat zijn sporen van de aanvaller.

## De denkwijze

1. **Eerst indammen:** de gelekte sleutel intrekken (in de code, en dan `apply`). Bewijs het: probeer de oude sleutel en toon de `403`.
2. **Dan herstellen:** de app laat de nieuwe sleutel uit `core/` gebruiken, nooit meer een sleutel in een bestand in Git.
3. **Dan onderzoeken:** audit logs: wat deed de aanvaller met de sleutel? Elke actie noteren en terugdraaien.
4. **Least privilege:** welke S3-acties gebruikt `scrolls-app` echt? Alleen die blijven over.

!!! warning "Een sleutel uit de geschiedenis halen is niet genoeg"
    Ook als je het bestand aanpast, staat de oude sleutel nog in de Git-geschiedenis.
    Daarom moet je hem **intrekken** (roteren). Een ingetrokken sleutel in de geschiedenis is onschuldig.

## Wat we deden

De "keukenhulp" uit de opdracht bleek de **metrics-collector** in de cluster: een klein account dat alleen
nodes en pods moet oplijsten, maar via een binding **`cluster-admin`** was (alles mogen, ook alle Secrets lezen).

| Stap | Wat | Waar |
|---|---|---|
| Least privilege | Eén rol: `list nodes`, `list pods` en `GET /metrics`. De binding naar `cluster-admin` en de rol die alle Secrets las, zijn weg | `workload/charts/kube-monitoring/templates/rbac.yaml` |
| Account in code | Het service account staat in de chart, met een nieuwe naam. Een nieuw account maakt elke oude token ongeldig | `values.yaml`, `templates/serviceaccounts.yaml` |
| Secrets uit Git | De S3-sleutel en de signing key komen nu uit Terraform (`set_sensitive`), niet meer uit `scrolls.yaml` | `workload/monitoring.tf` |
| Roteren | Rotatieknoppen voor de S3-identiteit, het websitewachtwoord en de registry-user. Alles wat in de (leesbare) Terraform-state stond, geldt als gestolen | `core/iam.tf`, `workload/ingress.tf`, `core/registry.tf` |
| Schade onderzoeken | Bucket `scrolls`: leeg, ook geen versies, dus geen data kwijt. In de cluster: twee sporen van de aanvaller, opgeruimd door de Kubernetes-ghost-check | `docs/bewijs/level-2/20261124-1522-oude-s3-keys/` |

**Bewijs:** `can-i '*' '*'` van het oude account: `yes` → `no`. De oude token geeft *Unauthorized*. Alle oude S3-keys
geven `403`. Het kubeconfig-certificaat hebben we bewust nog niet gereset: bij OVH installeert dat alle nodes opnieuw.

!!! warning "Verwijderd is niet altijd meteen ongeldig"
    OVH aanvaardde verwijderde S3-keys nog een tijd. Pas toen we de hele gebruiker vervingen, werden ze geweigerd.
    Test dus altijd of een oude sleutel écht niet meer werkt.
