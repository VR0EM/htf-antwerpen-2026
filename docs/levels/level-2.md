# Level 2: Seal of the Shadow (gelekte sleutel)

**Eigenaar:** Wimme · **Issue:** #6

!!! info "Wimme vult aan"
    Deze pagina beschrijft wat we bij het lezen van de code al zagen. De uitwerking volgt.

## De opdracht in gewone taal

Een sleutel van een service account is uitgelekt en dat account kan te veel. Maak de oude sleutel
**ongeldig**, maak een nieuwe die **veilig bewaard** wordt, zoek uit wat de aanvaller deed, en geef het
account enkel de rechten die het nodig heeft. Alles in code.

## Wat we al zagen

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
