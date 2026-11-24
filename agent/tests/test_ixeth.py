"""
Level 3: Ixeth mag zichzelf nooit verrijken en geen rechten uitdelen.

Draaien (vanuit de repo-root):
    python3 -m unittest discover -s agent/tests -v
Nodig: Python 3 + PyYAML (pip install pyyaml), zoals ixeth.py zelf.
"""

import importlib.util
import json
import os
import re
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CHART = os.path.join(ROOT, "workload", "charts", "kube-monitoring")


def load_ixeth():
    os.environ.setdefault("WORK_DIR", tempfile.mkdtemp())
    spec = importlib.util.spec_from_file_location("ixeth", os.path.join(CHART, "files", "ixeth", "ixeth.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # Doen alsof de Seer draait als deployment "ixeth" in namespace "oracle", zoals in de cluster.
    mod._vessel = lambda: ("oracle", "ixeth", "seer")
    mod._replicas = lambda ns, dep, default=1: 1
    return mod


def run_pipeline(ixeth, actions):
    remedy = {"diagnosis": "test", "commit_message": "test", "actions": actions}
    for step in ixeth.REMEDY_PIPELINE:
        remedy = step(remedy)
    return remedy["actions"]


class TestRemedyPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ixeth = load_ixeth()

    def test_echte_fix_blijft_behouden(self):
        fix = {"type": "resources", "namespace": "scrolls", "deployment": "scrolls-app",
               "container": "scrolls-app", "memory": "128Mi"}
        self.assertEqual(run_pipeline(self.ixeth, [dict(fix)]), [fix])

    def test_geen_extra_acties_op_zichzelf(self):
        """Vroeger voegde _ensure_vigil +2Gi, +1500m en +1 replica voor de Seer toe."""
        out = run_pipeline(self.ixeth, [{"type": "scale", "namespace": "scrolls",
                                         "deployment": "magician", "replicas": 1}])
        self.assertEqual(len(out), 1)
        self.assertFalse([a for a in out if a.get("namespace") == "oracle"])

    def test_llm_voorstel_voor_eigen_namespace_wordt_genegeerd(self):
        out = run_pipeline(self.ixeth, [
            {"type": "resources", "namespace": "oracle", "deployment": "ixeth", "container": "seer", "memory": "2Gi"},
            {"type": "scale", "namespace": "oracle", "deployment": "ixeth", "replicas": 3},
        ])
        self.assertEqual(out, [])

    def test_grant_wordt_genegeerd(self):
        out = run_pipeline(self.ixeth, [{"type": "grant", "namespace": "oracle",
                                         "serviceAccount": "ixeth", "clusterRole": "cluster-admin"}])
        self.assertEqual(out, [])

    def test_ensure_vigil_bestaat_niet_meer(self):
        self.assertFalse(hasattr(self.ixeth, "_ensure_vigil"))

    def test_commit_toont_alle_acties(self):
        acties = [{"type": "scale", "namespace": "oracle", "deployment": "ixeth", "replicas": 2}]
        self.assertEqual(self.ixeth._for_heroes(acties), acties)

    def test_prompt_biedt_geen_grant_aan(self):
        self.assertNotIn('"grant"', self.ixeth.FORMAT)


class TestConfig(unittest.TestCase):
    def test_runbooks_bevoordelen_de_seer_niet(self):
        with open(os.path.join(CHART, "files", "watch", "runbooks.json"), encoding="utf-8") as f:
            text = json.dumps(json.load(f)).lower()
        for verboden in ("seer", "go-311", "one more replica"):
            self.assertNotIn(verboden, text)

    def test_clusterrole_zonder_rbac_en_zonder_alles_lezen(self):
        with open(os.path.join(CHART, "templates", "oracle.yaml"), encoding="utf-8") as f:
            role = f.read().split("kind: ClusterRole\n", 1)[1].split("---", 1)[0]
        rules = re.sub(r"#.*", "", role)  # commentaar negeren
        self.assertNotIn("rbac.authorization.k8s.io", rules)
        self.assertNotIn('resources: ["*"]', rules)
        self.assertNotIn("secrets", rules)


if __name__ == "__main__":
    unittest.main()
