"""Regression tests for triage.py and eval.py. Stdlib only, no Claude CLI needed —
subprocess calls are stubbed. Run with: python3 -m unittest -v"""

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import eval as scorer
import triage


def ticket(tid: str, severity: str = "P2", routing: str = "Tier 1 Support") -> dict:
    return {"id": tid, "author_role": "resident", "text": f"ticket {tid}",
            "true_severity": severity, "true_routing": routing}


def write_jsonl(path: Path, rows: list) -> None:
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def read_jsonl(path: Path) -> list:
    return [json.loads(l) for l in path.read_text().splitlines()]


def cli_returning(result: str):
    """Stand-in for subprocess.run that mimics `claude -p ... --output-format json`."""
    def run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, json.dumps({"result": result}), "")
    return run


class TriageTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.data = Path(tmp.name) / "tickets.jsonl"
        self.out = Path(tmp.name) / "predictions.jsonl"

    def run_triage(self, **patches):
        with mock.patch.multiple(triage, DATA_PATH=self.data, OUTPUT_PATH=self.out, **patches), \
                contextlib.redirect_stderr(io.StringIO()):
            triage.main()

    def test_rerun_retries_tickets_that_failed(self):
        write_jsonl(self.data, [ticket("T001"), ticket("T002"), ticket("T003")])
        write_jsonl(self.out, [
            {"id": "T001", "severity": "P2", "routing": "Tier 1 Support"},
            {"id": "T002", "error": "claude CLI exited 1: not logged in"},
        ])
        classify = mock.Mock(return_value={"severity": "P2", "routing": "Tier 1 Support"})
        self.run_triage(classify=classify)

        retried = [c.args[0]["id"] for c in classify.call_args_list]
        self.assertEqual(retried, ["T002", "T003"])
        latest = {r["id"]: r for r in read_jsonl(self.out)}  # later rows win, as in eval.py
        self.assertFalse([pid for pid, r in latest.items() if "error" in r])


if __name__ == "__main__":
    unittest.main()
