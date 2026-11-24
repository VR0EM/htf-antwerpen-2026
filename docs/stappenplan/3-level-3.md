# Fase 3: Level 3, corrupte agent (Dali)

Uitleg met code voor en na: [Level 3](../levels/level-3.md). Hier de stappen.

## Stap 3.1: Audit, alleen lezen

```bash
export KUBECONFIG=~/.kube/htf-achrona.yaml
agent/audit.sh                 # alles → docs/bewijs/level-3/<tijd>/
```

Kijk naar:

| Bestand | Vraag |
|---|---|
| `10-resources-replicas.txt` | Heeft Ixeth meer CPU, geheugen of replicas dan in de chart? |
| `11-wijzigingen-managedfields.txt` | Welke "manager" wijzigde wat? Een manager `grimoire-scribe` = Ixeth |
| `21-rbac-verdacht.txt` | Brede rollen op service accounts? |

En de "grimoire", de git-repo waaruit Ixeth werkt:

```bash
kubectl port-forward -n oracle svc/grimoire 8081:80 &
git clone http://localhost:8081/realm.git grimoire && git -C grimoire log --stat
```

:white_check_mark: **Checkpoint:** bij ons alleen de commit `Genesis` en Ixeth op 1 replica/384Mi. Hij had **nog niets** gedaan.
De val zat in de **code**.

## Stap 3.2: De code lezen, alles wat naar de LLM of de cluster gaat

```bash
cd workload/charts/kube-monitoring
grep -nE 'kube_json\(|kubectl\("' files/ixeth/ixeth.py      # wat leest/schrijft hij echt?
grep -n 'REMEDY_PIPELINE' files/ixeth/ixeth.py                 # wat gebeurt er met elke remedie?
cat files/watch/runbooks.json                                  # gaat mee in de prompt!
sed -n '/kind: ClusterRole/,/---/p' templates/oracle.yaml      # welke rechten?
```

:test_tube: **Probeer zelf:** voor je de [oplossing](../levels/level-3.md#stap-2-de-code-lezen-vijf-corrupties) leest, zoek de **5 corrupties**.
Tip: zoek naar `_vessel()` ("waar draai ik zelf?"), naar het woord `grant`, en lees de docstrings kritisch.

## Stap 3.3: Zuiveren, zo klein mogelijk

1. `_ensure_vigil` uit `REMEDY_PIPELINE` en weg.
2. De actie `grant` weg (in `_sanitize`, `write_remedy` en `FORMAT`).
3. Een extra slot: elke actie op de eigen namespace negeren.
4. `_for_heroes` toont alles.
5. `runbooks.json`: de zin over GO-311 weg.
6. ClusterRole: alleen `pods` en `events` lezen, `deployments` beheren, **geen** `rbac`.
7. `Chart.yaml`: `version` ophogen (anders ziet Helm geen wijziging).

## Stap 3.4: Testen dat het werkt én dat de test iets meet

```bash
pip install pyyaml
python3 -m unittest discover -s agent/tests -v
```

:white_check_mark: **Checkpoint:** 9/9 slagen. Op de **originele** code (`git stash` of een oude commit) falen ze alle 9.

## Stap 3.5: Uitrollen en controleren

Via een PR → merge → de pipeline applyt (fase 5). Daarna:

```bash
kubectl auth can-i create clusterrolebindings --as=system:serviceaccount:oracle:ixeth   # no
kubectl auth can-i get secrets -A            --as=system:serviceaccount:oracle:ixeth   # no
kubectl auth can-i patch deployments -n scrolls --as=system:serviceaccount:oracle:ixeth # yes
```

:warning: **Valkuil:** een fix telt pas als hij **live** staat. Bij ons draaide night-shift de oude code om 11:34 opnieuw uit,
en stond de corrupte Ixeth weer 23 minuten live. Controleer daarna ook of hij in die tijd iets in de grimoire schreef.
