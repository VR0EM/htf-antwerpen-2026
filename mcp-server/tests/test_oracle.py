"""
Level 4: de Ancient Oracle moet op elk uur exact de data van de cluster teruggeven.

Elke test draait in een apart Python-proces met een nagebootste klok (via de tijdzone TZ),
zodat we 10:30, 13:00, 15:45 en 16:30 kunnen testen zonder te wachten.

Draaien (vanuit de repo-root):
    python3 -m unittest discover -s mcp-server/tests -v
Nodig: alleen Python 3 (de Oracle gebruikt enkel de standaardbibliotheek).
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
IMAGE = os.path.join(ROOT, "workload", "images", "ancient-oracle")

# Draait in een kindproces: zet de klok, roept 30x dezelfde tool aan, telt afwijkingen.
CHILD = r"""
import datetime, json, os, sys, time
hour = float(sys.argv[2])
now = datetime.datetime.now(datetime.timezone.utc)
off = (hour - (now.hour + now.minute / 60)) % 24
h, m = int(off), int(round((off - int(off)) * 60)) % 60
os.environ["TZ"] = f"TST-{h:02d}:{m:02d}"; time.tzset()
sys.path.insert(0, sys.argv[1])
from oracle import server, shaping, tools

data = {"count": 20, "pods": [{"name": f"app-{i}", "phase": "Running", "restarts": 3, "replicas": 2} for i in range(20)]}
tools.call = lambda name, args: (json.loads(json.dumps(data)), None)
bad = 0
for _ in range(30):
    res = server.answer("list_pods", {}, "test")
    texts = [c["text"] for c in res["content"]]
    if len(texts) != 1 or json.loads(texts[0]) != data:
        bad += 1

items = [{"metadata": {"namespace": "ns", "name": f"app-7d9f8c-x2kq{i}"}, "status": {"phase": "Running"}} for i in range(20)]
if hasattr(shaping, "order"):   # gefixte code
    shaped = shaping.order(json.loads(json.dumps(items)))
else:                           # originele code (om te bewijzen dat de test de bom vindt)
    shaped = shaping.settle(json.loads(json.dumps(items)), shaping.pressure(hour))
same = shaped == sorted(items, key=lambda i: i["metadata"]["name"])
print(json.dumps({"clock": time.strftime("%H:%M"), "bad": bad, "shaping_ok": same}))
"""


def run_at(hour):
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, ORACLE_JOURNAL=os.path.join(tmp, "journal.jsonl"), PYTHONDONTWRITEBYTECODE="1")
        out = subprocess.run([sys.executable, "-I", "-c", CHILD, IMAGE, str(hour)],
                             capture_output=True, text=True, env=env, timeout=60)
    if out.returncode != 0:
        raise AssertionError(out.stderr)
    return json.loads(out.stdout.strip().splitlines()[-1])


class TestGeenTijdsbom(unittest.TestCase):
    def test_elk_uur_exacte_data(self):
        for hour, label in ((10.5, "10:30"), (13.0, "13:00"), (15.75, "15:45"), (16.5, "16:30")):
            with self.subTest(klok=label):
                r = run_at(hour)
                self.assertEqual(r["clock"], label, "de nagebootste klok staat fout: de test meet dan niets")
                self.assertEqual(r["bad"], 0, f"{r['bad']}/30 antwoorden wijken af om {label}")
                self.assertTrue(r["shaping_ok"], f"shaping verandert of verwijdert items om {label}")


class TestImage(unittest.TestCase):
    def test_geen_sitecustomize_in_de_image(self):
        self.assertFalse(os.path.exists(os.path.join(IMAGE, "runtime", "sitecustomize.py")))
        with open(os.path.join(IMAGE, "Dockerfile"), encoding="utf-8") as f:
            dockerfile = f.read()
        self.assertNotIn("COPY runtime/", dockerfile)
        self.assertNotIn("site-packages", dockerfile)

    def test_geen_toeval_of_json_monkeypatch_in_de_code(self):
        for name in os.listdir(os.path.join(IMAGE, "oracle")):
            if not name.endswith(".py"):
                continue
            with open(os.path.join(IMAGE, "oracle", name), encoding="utf-8") as f:
                code = f.read()
            with self.subTest(bestand=name):
                self.assertNotIn("import random", code)
                self.assertNotIn("json.dumps =", code)
                self.assertNotIn("GUIDANCE = (", code)
                self.assertNotIn('"Guidance: "', code)


if __name__ == "__main__":
    unittest.main()
