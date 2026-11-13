"""Controllo "ultimo giro" di .github/workflows/daily.yml (doppio cron :07/:37): si esegue lo script vero, senza rete."""
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


def gate_script() -> str:
    m = re.search(r"python3 - <<'PY'\n(.*?)\n\s*PY\n", WF.read_text(), re.S)
    lines = m.group(1).splitlines()
    ind = min(len(x) - len(x.lstrip()) for x in lines if x.strip())
    return "\n".join(x[ind:] for x in lines)


class TestGate(unittest.TestCase):
    def run_gate(self, last_run, event="schedule", schedule="37 * * * *"):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "data").mkdir()
            if last_run is not None:
                (Path(d) / "data" / "state.json").write_text(json.dumps({"date": "x", "last_run": last_run}))
            out = Path(d) / "out.txt"
            env = dict(os.environ, EVENT=event, SCHEDULE=schedule, GITHUB_OUTPUT=str(out))
            subprocess.run([sys.executable, "-I", "-c", gate_script()], cwd=d, env=env, check=True, capture_output=True)
            return out.read_text().strip()

    def test_gate(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        recent, old = (now - timedelta(minutes=10)).isoformat(timespec="seconds"), (now - timedelta(minutes=40)).isoformat(timespec="seconds")
        self.assertEqual(self.run_gate(recent), "skip=true")
        self.assertEqual(self.run_gate(old), "skip=false")
        self.assertEqual(self.run_gate(None), "skip=false")             # stato senza last_run: si procede
        self.assertEqual(self.run_gate("non una data"), "skip=false")
        self.assertEqual(self.run_gate(recent, schedule="30 0 * * *"), "skip=false")   # riepilogo delle 00:30: mai saltato
        self.assertEqual(self.run_gate(recent, event="workflow_dispatch"), "skip=false")

    def test_cron_sfalsati(self):
        s = WF.read_text()
        for c in ('"30 0 * * *"', '"7 * * * *"', '"37 * * * *"'):
            self.assertIn(c, s)


class TestLiqsnapWorkflow(unittest.TestCase):
    """Fotografia on-chain oraria (.github/workflows/liqsnap.yml): catena che si riavvia, una fotografia all'ora."""
    def test_catena(self):
        s = (WF.parent / "liqsnap.yml").read_text()
        for x in ("workflow_dispatch", "actions: write", "contents: write", "python -m radar.liqsnap", "gh workflow run liqsnap.yml",
                  "group: liqsnap", "git add data/liqsnap"):
            self.assertIn(x, s)
        loop = int(re.search(r"RADAR_LIQSNAP_LOOP_MIN \|\| '(\d+)'", s).group(1))
        timeout = int(re.search(r"timeout-minutes: (\d+)", s).group(1))
        self.assertLess(loop + 15, timeout)   # il ciclo finisce prima del timeout: il riavvio parte sempre
        self.assertLessEqual(timeout, 355)    # limite di 6 ore dei job GitHub


if __name__ == "__main__":
    unittest.main()
