"""Workflow: controllo "ultimo giro" e scelta dello stato di daily.yml (si eseguono gli script veri, senza rete), catena di
liqsnap.yml, niente -X theirs, requirements fissati, YAML valido."""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

WF = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "daily.yml"


def step_script(name: str) -> str:
    """Script Python (heredoc PY) del passo `name` di daily.yml."""
    txt = WF.read_text()
    m = re.search(r"- name: " + re.escape(name) + r"\n.*?python3 - <<'PY'\n(.*?)\n\s*PY\n", txt, re.S)
    lines = m.group(1).splitlines()
    ind = min(len(x) - len(x.lstrip()) for x in lines if x.strip())
    return "\n".join(x[ind:] for x in lines)


def gate_script() -> str:
    return step_script("Controllo ultimo giro")


class TestGate(unittest.TestCase):
    def run_gate(self, last_run, event="schedule", gate=None):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "data").mkdir()
            if last_run is not None:
                (Path(d) / "data" / "state.json").write_text(json.dumps({"date": "x", "last_run": last_run}))
            out = Path(d) / "out.txt"
            env = dict(os.environ, EVENT=event, GITHUB_OUTPUT=str(out))
            env.pop("GATE", None)
            if gate is not None:
                env["GATE"] = gate
            subprocess.run([sys.executable, "-I", "-c", gate_script()], cwd=d, env=env, check=True, capture_output=True)
            return out.read_text().strip()

    def test_gate(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        recent, old = (now - timedelta(minutes=10)).isoformat(timespec="seconds"), (now - timedelta(minutes=40)).isoformat(timespec="seconds")
        self.assertEqual(self.run_gate(recent), "skip=true")
        self.assertEqual(self.run_gate(old), "skip=false")
        self.assertEqual(self.run_gate(None), "skip=false")             # stato senza last_run: si procede
        self.assertEqual(self.run_gate("non una data"), "skip=false")
        self.assertEqual(self.run_gate(recent, event="workflow_dispatch"), "skip=false")             # manuale: mai saltato
        self.assertEqual(self.run_gate(recent, event="workflow_dispatch", gate="false"), "skip=false")
        self.assertEqual(self.run_gate(recent, event="workflow_dispatch", gate="true"), "skip=true")  # catena liqsnap.yml
        self.assertEqual(self.run_gate(old, event="workflow_dispatch", gate="true"), "skip=false")

    def test_cron_sfalsati(self):
        s = WF.read_text()
        for c in ('"7 * * * *"', '"37 * * * *"'):
            self.assertIn(c, s)
        self.assertNotIn('"30 0 * * *"', s)                       # il riepilogo non dipende più da un cron (M4)
        self.assertIn("RADAR_DAILY_BRIEF: ${{ vars.RADAR_DAILY_BRIEF || '1' }}", s)
        self.assertIn("gate:", s)


class TestStateRestore(unittest.TestCase):
    """Stato salvato in cache dopo un push fallito (M6): si usa solo se più recente (last_run) di quello del repository."""
    def run_choice(self, repo, cache):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "data").mkdir()
            (Path(d) / ".state-cache").mkdir()
            for p, v in ((Path(d) / "data" / "state.json", repo), (Path(d) / ".state-cache" / "state.json", cache)):
                if v is not None:
                    p.write_text(v if isinstance(v, str) else json.dumps(v))
            subprocess.run([sys.executable, "-I", "-c", step_script("Scelta dello stato più recente")], cwd=d, check=True,
                           capture_output=True)
            f = Path(d) / "data" / "state.json"
            return json.loads(f.read_text()) if f.exists() else None

    def test_scelta(self):
        a = {"last_run": "2026-11-13T10:07:00", "weekly": {"x": 1}}
        b = {"last_run": "2026-11-13T11:07:00", "weekly": {"x": 2}}
        self.assertEqual(self.run_choice(a, b), b)          # cache più recente: ripristinata
        self.assertEqual(self.run_choice(b, a), b)          # cache vecchia: resta il repository
        self.assertEqual(self.run_choice(b, b), b)
        self.assertEqual(self.run_choice(a, None), a)       # nessuna cache
        self.assertEqual(self.run_choice(a, "{rotto"), a)   # cache illeggibile: ignorata
        self.assertEqual(self.run_choice(None, b), b)       # repository senza stato: si usa la cache
        self.assertEqual(self.run_choice(a, {"weekly": {}}), a)   # cache senza last_run: ignorata

    def test_passi_push_e_cache(self):
        s = WF.read_text()
        self.assertIn("for i in 1 2 3 4 5", s)
        self.assertIn("key: radar-state-${{ github.run_id }}", s)
        self.assertIn("restore-keys: radar-state-", s)
        self.assertIn("steps.push.outcome == 'failure'", s)
        self.assertIn("Avviso push fallito", s)

    def test_deploy_con_secondo_tentativo(self):
        s = WF.read_text()
        self.assertEqual(s.count("uses: actions/deploy-pages@v4"), 2)
        self.assertIn("steps.deploy.outcome == 'failure'", s)
        self.assertIn("sleep 30", s)
        dep = s[s.index("- id: deploy\n"):s.index("- name: Attesa prima")]
        self.assertIn("continue-on-error: true", dep)


class TestAllWorkflows(unittest.TestCase):
    def test_niente_theirs_e_requirements(self):
        for f in WF.parent.glob("*.yml"):
            s = f.read_text()
            self.assertFalse("-X theirs" in s, f.name)   # perdeva membri gzip in silenzio (M5)
            if "pip install" in s:
                self.assertIn("pip install -r requirements.txt", s, f.name)
        req = [x for x in (WF.parents[2] / "requirements.txt").read_text().splitlines() if x.strip() and not x.startswith("#")]
        self.assertTrue(req)
        for x in req:
            self.assertRegex(x, r"^[A-Za-z0-9_.-]+==[0-9][0-9.]*$")

    def test_yaml_valido(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML non installato")
        for f in WF.parent.glob("*.yml"):
            d = yaml.safe_load(f.read_text())
            self.assertIn("jobs", d, f.name)


class TestLiqsnapWorkflow(unittest.TestCase):
    """Fotografia on-chain oraria (.github/workflows/liqsnap.yml): catena che si riavvia, una fotografia all'ora."""
    def test_catena(self):
        s = (WF.parent / "liqsnap.yml").read_text()
        for x in ("workflow_dispatch", "actions: write", "contents: write", "python -m radar.liqsnap", "gh workflow run liqsnap.yml",
                  "group: liqsnap", "git add data/liqsnap"):
            self.assertIn(x, s)
        loop = int(re.search(r"RADAR_LIQSNAP_LOOP_MIN \|\| '(\d+)'", s).group(1))
        self.assertLessEqual(loop, 320)
        self.assertIn('[ "$LOOP_MIN" -le 320 ] 2>/dev/null || LOOP_MIN=320', s)   # tetto anche con la variabile più alta
        self.assertIn("gh workflow run daily.yml", s)                              # orologio orario di daily.yml (M4)
        self.assertIn("-f gate=true", s)
        self.assertIn("python -m radar.liqsnap sync", s)
        self.assertIn("if: failure()", s)
        self.assertIn("gh workflow disable", s)
        timeout = int(re.search(r"timeout-minutes: (\d+)", s).group(1))
        self.assertLess(loop + 15, timeout)   # il ciclo finisce prima del timeout: il riavvio parte sempre
        self.assertLessEqual(timeout, 355)    # limite di 6 ore dei job GitHub


if __name__ == "__main__":
    unittest.main()
