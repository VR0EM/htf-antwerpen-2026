"""
Kubernetes-ghost-check (#57): Helm-drift herkennen en het juiste manifest terugvinden.

Draaien (vanuit de repo-root):
    python3 -m unittest discover -s agent/tests -v
"""

import base64
import gzip
import importlib.util
import json
import os
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def load():
    spec = importlib.util.spec_from_file_location("ghost", os.path.join(ROOT, "ci", "k8s-ghost-check.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def mf(*entries):
    return {"metadata": {"managedFields": [{"manager": m, "time": t} for m, t in entries]}}


LEDGER = """# Source: kube-monitoring/templates/scrolls.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: scrolls-ledger
  namespace: scrolls
  labels:
    app.kubernetes.io/part-of: scrolls
    app.kubernetes.io/name: kube-monitoring
data:
  megabytes: "12"
"""

ROLE = """apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  labels:
    app.kubernetes.io/name: oracle
  name: ixeth-seer
rules: []
"""


class TestHelmDrift(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = load()

    def test_ledger_van_14u26_wordt_herkend(self):
        """Echte managedFields van scrolls-ledger om 14:26."""
        obj = mf(("terraform-provider-helm_v3.3.0_x5", "2026-11-24T13:24:01Z"),
                 ("kubectl-patch", "2026-11-24T13:26:49Z"))
        self.assertEqual(self.g.hand_edited(obj), ("kubectl-patch", "2026-11-24T13:26:49Z"))

    def test_na_helm_upgrade_geen_drift(self):
        obj = mf(("kubectl-patch", "2026-11-24T13:26:49Z"),
                 ("terraform-provider-helm_v3.3.0_x5", "2026-11-24T13:59:35Z"))
        self.assertIsNone(self.g.hand_edited(obj))

    def test_eigen_herstel_telt_als_helm(self):
        obj = mf(("kubectl-patch", "2026-11-24T13:26:49Z"), ("k8s-ghost-check", "2026-11-24T13:30:00Z"))
        self.assertIsNone(self.g.hand_edited(obj))

    def test_scribe_en_rollout_zijn_geen_handwerk(self):
        obj = mf(("terraform-provider-helm_v3.3.0_x5", "2026-11-24T13:24:01Z"),
                 ("grimoire-scribe", "2026-11-24T13:40:00Z"), ("kubectl-rollout", "2026-11-24T13:41:00Z"))
        self.assertIsNone(self.g.hand_edited(obj))

    def test_manifest_uit_helm_release(self):
        release = {"name": "monitoring", "namespace": "observability", "manifest": "---\n" + LEDGER + "---\n" + ROLE}
        packed = base64.b64encode(base64.b64encode(gzip.compress(json.dumps(release).encode()))).decode()
        self.g.kubectl = lambda *a: json.dumps({"items": [{"data": {"release": packed}}]})
        docs = self.g.releases()
        self.assertIn(("ConfigMap", "scrolls", "scrolls-ledger"), docs)
        self.assertIn(("ClusterRole", "observability", "ixeth-seer"), docs)  # ns ongebruikt voor cluster-objecten
        self.assertIn('megabytes: "12"', docs[("ConfigMap", "scrolls", "scrolls-ledger")][1])


if __name__ == "__main__":
    unittest.main()
