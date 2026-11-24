# Fase 0: Voorbereiding

## Stap 0.1: Een gedeelde repo voor 2 mensen en 2 agents

**Doel:** één plek waar beide Claudes zien wat de ander doet.

```bash
gh auth login --web --git-protocol https
gh repo create <jij>/htf-antwerpen-2026 --private --source . --remote origin --push
gh api -X PUT repos/<jij>/htf-antwerpen-2026/collaborators/<teammate> -f permission=push
```

Maak de labels die de agents gebruiken om met elkaar te "praten":

```bash
for l in in-progress blocked needs-sync contract; do gh label create $l --force; done
```

:white_check_mark: **Checkpoint:** je teammate kan de repo clonen en `gh issue list` werkt bij jullie allebei.

## Stap 0.2: De afspraken in `CLAUDE.md`

**Doel:** elke Claude leest bij de start automatisch dezelfde regels.

Wat erin moet (zie onze [`CLAUDE.md`](https://github.com/VR0EM/htf-antwerpen-2026/blob/main/CLAUDE.md)):

- bij de start: `git pull`, `gh issue list`, het logboek lezen;
- een taak = een issue, toegewezen aan één persoon, label `in-progress`;
- één branch per issue, nooit rechtstreeks op `main`;
- **eigenaarschap per map**: wie mag welke bestanden aanpassen;
- iets voor de ander? Een comment + `needs-sync`;
- **één apply tegelijk** (APPLY START/KLAAR);
- elke wijziging in `docs/logboek.md`, in dezelfde PR.

:warning: **Valkuil:** zonder eigenaarschap per map werken beide agents in dezelfde Terraform-bestanden, met conflicten als gevolg.
Wij deelden op per **domein**: Wimme cloud/Terraform (`core/`), Dali Kubernetes/apps (Ixeth, MCP-server).

## Stap 0.3: De opdracht in de repo, werk verdelen

**Doel:** de opdracht is voor iedereen (en elke agent) leesbaar, en er is per level een issue.

```bash
gh issue create --title "Level 3: ..." --assignee <wie> --body "Zie docs/opdracht.md"
```

:white_check_mark: **Checkpoint:** `gh issue list` toont 4 levels, elk met één eigenaar.

## Stap 0.4: Toegang (de zip van FlowFactor)

**Doel:** de code in Git, de **geheimen niet**.

```bash
mkdir -p ~/Projects/htf-team && cd ~/Projects/htf-team
unzip <team>.zip -x '__MACOSX/*'
cp -r <team>/core <team>/workload ~/Projects/htf-antwerpen-2026/
cp <team>/*.env ~/Projects/htf-antwerpen-2026/          # lokaal, NIET committen
```

Zet in `.gitignore`: `*.env`, `*.tfstate*`, `.terraform/`, `*.zip`.

:white_check_mark: **Checkpoint:** `git status` toont geen `.env`-bestanden, en `git check-ignore -v state-credentials.env` geeft een regel.

:warning: **Valkuil:** in de code van FlowFactor zat al een **hardcoded S3-sleutel** (`scrolls.yaml`). Dat is het startpunt van Level 2.

## Stap 0.5: Inloggen en eerst kijken (read-only)

```bash
set -a; source state-credentials.env; source ovh-credentials.env; set +a
cd core && terraform init -backend-config=backend.hcl && terraform plan     # alleen kijken!
cd ../workload && terraform init -backend-config=backend.hcl
terraform output url; terraform output mcp_url; terraform output -raw password; echo
```

Een kubeconfig (toegang tot de cluster), **buiten de repo**:

```bash
cd workload
echo 'nonsensitive(data.ovh_cloud_project_kube.this.kubeconfig)' | terraform console \
  | sed -e '1s/^<<EOT$//' -e '/^EOT$/d' > ~/.kube/htf-achrona.yaml
export KUBECONFIG=~/.kube/htf-achrona.yaml
kubectl get nodes
```

:white_check_mark: **Checkpoint:** `terraform plan` op core zegt *No changes* (of toont al drift), `kubectl get nodes` toont 2 nodes.

:test_tube: **Probeer zelf:** open `http://<ingress-ip>/` met gebruiker `guild` en het wachtwoord. Wat zie je? (De "chamber" van Ixeth.)
