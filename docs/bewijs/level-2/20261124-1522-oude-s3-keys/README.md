# Oude S3-keys van scrolls_app en schade aan de bucket (VR0EM, 15:22)

Alle keys komen uit de Helm-geschiedenis van `kube-monitoring` (de waarden van elke release).
Enkel de eerste 8 tekens staan hier. Getest met een S3-request (SigV4, `ListObjectsV2`).

| Key | In gebruik sinds | OVH-API (15:23) | Bucket `scrolls` | State-bucket |
|---|---|---|---|---|
| `99e911c5…` | 10:09 (origineel, stond in de gestolen state) | **verwijderd** | **200** (nog aanvaard) | 403 |
| `e9fb7aa3…` | 14:59 (rotatie-2) | **verwijderd** | **200** (nog aanvaard) | 403 |
| `01df9ea4…` | 15:08 (per ongeluk, 4 min) | verwijderd | 403 | 403 |
| `750545b1…` | 15:12 (huidig) | bestaat | 200 | **403** |

- **Het lek van golf 1/4 is dicht:** geen enkele key van `scrolls_app` kan nog de state-bucket lezen (policy terug enkel op `scrolls`).
- **Revocatie bij OVH is traag:** keys die al gebruikt waren, blijven werken lang nadat de API ze verwijderde. Een key die nooit gebruikt werd, valt meteen weg. Vermoedelijk een cache in de S3-dienst.
- **Reactie:** de rotatie vervangt nu de hele gebruiker (`core/iam.tf`, `rotatie-4-nieuwe-user`). De oude keys verliezen zo hun eigenaar en hun policy.

## Schade aan de bucket `scrolls`

OVH-API: `objectsCount 0`, `objectsSize 0`, 0 objecten, ook met `withVersions=true`. Versioning `enabled`, encryptie `AES256`.
De bucket was leeg en is leeg: er is geen data gelezen, gewijzigd of gewist.

## Na de nieuwe identiteit (#72, apply 15:26–15:28)

OVH-API om 15:29: gebruiker `achrona-scrolls-app` is nu `1015263` (aangemaakt 15:26) met enkel key `d2ab2e20…`. De oude gebruiker `1013904` is weg.

| Key | 15:22 | **15:29** |
|---|---|---|
| `99e911c5…` (origineel, in de gestolen state) | 200 | **403** |
| `e9fb7aa3…` (14:59, nooit in een leesbare state) | 200 | 200 (gebruiker pas 3 min weg) |
| `01df9ea4…` | 403 | 403 |
| `750545b1…` | 200 | **403** |
| `d2ab2e20…` (nieuw, in de app) | - | 200 |

Om **15:30:38**: `e9fb7aa3…` → **403**. Daarmee worden alle oude keys geweigerd. Enkel `d2ab2e20…` (de app) werkt.
