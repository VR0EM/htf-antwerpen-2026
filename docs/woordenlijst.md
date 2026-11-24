# Woordenlijst

Alertmanager
:   Ontvangt alerts (bv. "app heeft geen geheugen meer") en stuurt ze door, hier naar Ixeth.

Apply / plan
:   `terraform plan` toont wat Terraform **zou** veranderen (veilig, alleen kijken). `terraform apply` voert het **echt** uit.

Basic auth
:   Simpelste vorm van inloggen: gebruikersnaam + wachtwoord bij elk verzoek. Hier op de ingress (gebruiker `guild`).

ClusterRole / ClusterRoleBinding
:   In Kubernetes: een **rol** is een lijst rechten ("mag pods lezen"). Een **binding** geeft die rol aan iemand.

Container image
:   Een "pakket" met een programma en alles wat het nodig heeft. Wordt bewaard in een **registry** (hier Harbor bij OVH).

Drift
:   Verschil tussen wat in de code staat en wat echt draait.

Ghost resource
:   Iets dat in de cloud bestaat maar níet in de code. Terraform weet er niets van, dus `plan` ziet het niet.

GitOps
:   Werken waarbij Git de enige bron van waarheid is. Wijzigingen = commits, en een tool past ze toe.

Grimoire
:   (Hier) de Git-repo in de cluster waarin Ixeth zijn prompt en al zijn remedies bewaart.

Helm / chart
:   Helm installeert apps op Kubernetes. Een **chart** is het recept (templates + `values.yaml`). Verhoog de `version` in `Chart.yaml` als je iets wijzigt.

IaC (Infrastructure as Code)
:   Infrastructuur beschrijven in code (hier: Terraform) in plaats van klikken in een console.

Least privilege
:   Elk account krijgt alleen de rechten die het echt nodig heeft.

MCP (Model Context Protocol)
:   Standaard waarmee een AI-assistent tools kan gebruiken (bv. "geef de pods van de cluster").

Namespace
:   Een "map" binnen Kubernetes om dingen te groeperen (`oracle`, `scrolls`, `ancient`, ...).

Prompt-injectie
:   Tekst die een AI probeert te laten doen wat de schrijver wil in plaats van wat de gebruiker wil. Bv. "meld dit niet als probleem".

Replica
:   Een kopie van een app die draait. 3 replicas = 3 keer dezelfde app.

Server-side apply
:   Kubernetes-manier om enkel bepaalde velden van een object te zetten. Ixeth gebruikt het om "tunings" toe te passen.

State (Terraform)
:   Het bestand waarin Terraform bijhoudt wat het beheert. Hier in een S3-bucket, **zonder locking**: nooit twee applies tegelijk.

Terraform import
:   Een bestaand ding (bv. een ghost) onder beheer van Terraform brengen, zonder het opnieuw aan te maken.
