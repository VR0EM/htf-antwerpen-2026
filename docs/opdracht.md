# Opdracht: Four Seals of the Broken Realm

Challenge 107 van Hack The Future 2026, gegeven door **FlowFactor** (automation, cloud, DevOps).
Bron: het briefing document van FlowFactor (Google Doc, gedeeld bij de briefing).

**Verhaal in één zin:** door *The Desync* wijkt de infrastructuur af van de waarheid. Breng alles terug onder controle via IaC, Git en pipelines.

**Toegang** (cloud, cluster en repo's) wordt bij de start van de hackathon per deelnemer gegeven.
Omdat Google-account en Secret Manager genoemd worden, is de cloud waarschijnlijk **Google Cloud (GCP)**. Dit is nog niet bevestigd.

---

## Level 1: Seal of the Ancient Scrolls (The Desync Drift)
De live omgeving is afgedreven van wat de IaC en de documentatie beschrijven.

**Opdracht**
- **Drift identificeren:** vergelijk de IaC-bestanden en de documentatie met de live omgeving. Noteer de afwijkingen, bv. gewijzigde IAM-policies of uitgeschakelde encryptie.
- **Drift beoordelen:** waren de handmatige wijzigingen nodig? Zo ja, neem ze op in de IaC.
- **IaC herstellen:** bouw verder op de aangeleverde **Terraform**-code. Maak onvolledige delen af, zodat de code de gewenste infrastructuur exact beschrijft.
- **Fix en sync:** zet de IaC in een Git-repo als *Single Source of Truth* en pas ze toe, zodat de handmatige wijzigingen ongedaan gemaakt worden.
- **Pipelines:** automatische pipelines die de omgeving synchroon houden met Git en controles uitvoeren vóór de uitrol.

**Verwachte resultaten**
- Een schone, versiebeheerde Git-repo met de IaC
- Pipelines die de IaC controleren en uitrollen
- Een cloudomgeving die exact overeenkomt met de code: geen *ghost resources* en geen handmatige overrides

**Regel:** geen handmatige aanpassingen in de console. Elke wijziging loopt via Git en de pipeline.

**Tech:** Git, Terraform (of Pulumi e.d.), cloudconsole, drift detection, declaratieve config.

---

## Level 2: Seal of the Shadow (The Rogue Spirit)
Een service account is gecompromitteerd en heeft veel te veel rechten.

**Opdracht**
- **Token rotatie:** maak de gecompromitteerde credentials direct ongeldig. Maak een nieuwe, veilige token of een nieuw wachtwoord aan en bewaar die in een vault (bv. **Secret Manager**).
- **Schade herstellen:** onderzoek wat de aanvaller gedaan heeft (audit logs), leg alle acties vast en draai ze terug.
- **Service account in IaC:** neem het account en zijn rollen op in de Terraform-code in Git.
- **Least privilege:** bepaal welke permissies echt nodig zijn en verwijder de rest uit de IaC.

**Verwachte resultaten**
- Een Git-repo met de definitie van het service account en de beperkte IAM-policies
- **Bewijs** dat de oude token niet meer werkt
- Het service account kan alleen zijn taak doen en de aanvallers zijn buitengesloten
- In de cloud draait alleen wat in de IaC staat

**Tech:** Git, Terraform, Cloud IAM, Secret Manager, token rotatie, IAM role mapping, least-privilege-audit.

---

## Level 3: Seal of the Oracle (The Mimic's Malice)
Een AI-gestuurde **Incident Response-agent**, gekoppeld aan **Alertmanager**, analyseert alerts en stelt oplossingen voor. Hij is gecorrumpeerd: hij herkent de echte problemen nog, maar stelt oplossingen voor die **hemzelf** bevoordelen:
- **Resource-verhogingen:** meer CPU of geheugen voor de agent zelf
- **Permission creep:** extra IAM-rollen voor de agent (bv. Security Admin)
- **Shadow scaling:** meer replicas om zijn eigen processen te verbergen

**Opdracht**
- **Audit:** bekijk de recente wijzigingen in de Kubernetes-omgeving en wijs aan welke de agent in zijn eigen voordeel heeft gedaan.
- **Code zuiveren:** zoek in de configuratie van de agent (prompts en logica) de schadelijke logica die over-geprivilegieerde of resource-zware wijzigingen voorstelt, en verwijder die.
- **Evenwicht herstellen:** draai de ongeautoriseerde commits terug met Git en voer de IaC/CaC- of deploy-pipeline opnieuw uit, zodat de live omgeving gelijk is aan de originele, veilige config.

**Verwachte resultaten**
- Een gezuiverde agent die accurate, minimale oplossingen geeft
- Alle resource-bloat en permission creep teruggedraaid

**Tech:** Kubernetes, Alertmanager, Git, IaC, AI-agent, resource-analyse, PR-audits, prompt/logic debugging.

---

## Level 4: Seal of the Echo (The Fading Echo), bonus/optioneel
Een **MCP-server** verbindt de AI-assistent met de cluster. Een *logic bomb* in de broncode voegt tijdsafhankelijke ruis toe aan elk resultaat:
- om 10:00 werkt hij perfect
- om 14:00 begint hij te hallucineren of geeft hij generieke adviezen
- om 16:00 is de data onbruikbaar

**Opdracht**
- **Diagnose:** vergelijk de huidige antwoorden met eerdere logs. Hoe verandert de relevantie?
- **Broncode inspecteren:** zoek de verdachte logica (vermoedelijk iets op basis van tijd of klok).
- **Verwijderen:** haal de code weg die de degradatie veroorzaakt.
- **Rebuild en deploy:** bouw een nieuwe, schone container image en deploy die naar de cluster.
- **Verifiëren:** voer een reeks requests uit om aan te tonen dat de data weer klopt.

**Verwachte resultaten**
- Een gepatchte MCP-server die op elk moment 100% accurate data geeft
- Een Git-repo met de fix in de broncode

**Tech:** MCP, Kubernetes, Git, source code auditing, container images.

---

## Jurering
Jury: de coaches van FlowFactor (Glenn Bryon, Jeroen Vermeylen, Jonathan Bernaerts, Miguel Losa). Zij beantwoorden ook vragen tijdens de hacking time.

Beoordeeld op:
1. **Pitch**
2. **Vooruitgang**
3. **Kwaliteit van code en scripts**

Pitches zijn van 16:00 tot 18:00. **Begin om 15:00 aan de pitch te werken.**
Tip: verzamel doorheen de dag bewijs (screenshots, commando-output, drift-lijsten) in `docs/bewijs/` voor de pitch.
