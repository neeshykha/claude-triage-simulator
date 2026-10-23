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

    def test_severity_outside_p1_to_p4_is_a_failure_not_a_prediction(self):
        write_jsonl(self.data, [ticket("T001")])
        answer = {"severity": "P1 - Critical", "routing": "Tier 1 Support", "reasoning": "x"}
        self.run_triage(subprocess=mock.Mock(run=cli_returning(json.dumps(answer))))

        rows = read_jsonl(self.out)
        self.assertEqual(len(rows), 1)
        self.assertIn("error", rows[0])

    def test_cli_runs_with_tools_disabled(self):
        write_jsonl(self.data, [ticket("T001")])
        answer = {"severity": "P2", "routing": "Tier 1 Support", "reasoning": "x"}
        run = mock.Mock(side_effect=cli_returning(json.dumps(answer)))
        self.run_triage(subprocess=mock.Mock(run=run))

        cmd = run.call_args.args[0]
        self.assertIn("--tools", cmd)
        self.assertEqual(cmd[cmd.index("--tools") + 1:], [""])

    def test_answer_missing_a_field_is_written_once_as_a_failure(self):
        write_jsonl(self.data, [ticket("T001")])
        answer = {"severity": "P2", "reasoning": "no routing field"}
        self.run_triage(subprocess=mock.Mock(run=cli_returning(json.dumps(answer))))

        rows = read_jsonl(self.out)
        self.assertEqual(len(rows), 1)
        self.assertIn("error", rows[0])


class EvalTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "data").mkdir()
        (self.root / "results").mkdir()

    def score(self, tickets: list, predictions: list, groups: list = ()) -> str:
        write_jsonl(self.root / "data" / "tickets.jsonl", tickets)
        write_jsonl(self.root / "predictions.jsonl", predictions)
        with mock.patch.multiple(scorer, ROOT=self.root, CONFUSABLE_GROUPS=list(groups)), \
                contextlib.redirect_stdout(io.StringIO()):
            scorer.main()
        return (self.root / "results" / "scorecard.md").read_text()

    def test_scorecard_is_written_when_every_ticket_failed(self):
        failure = "claude CLI exited 1: not logged in"
        card = self.score([ticket("T001"), ticket("T002")],
                          [{"id": "T001", "error": failure}, {"id": "T002", "error": failure}])

        self.assertIn("**Tickets scored:** 0/2 (2 failed to classify)", card)
        self.assertIn(f"- T001: {failure}", card)

    def test_confusable_audit_does_not_count_unscored_tickets_as_misses(self):
        tickets = [ticket("T001", "P3"), ticket("T002", "P3"), ticket("T003", "P3")]
        predictions = [
            {"id": "T001", "severity": "P3", "routing": "Tier 1 Support"},
            {"id": "T002", "error": "timed out"},
            # T003 was never classified (run interrupted)
        ]
        card = self.score(tickets, predictions, groups=[(["T001", "T002", "T003"], "Trap")])

        self.assertIn("- **Trap**: 1/1 correct (2 not scored)", card)
        self.assertIn("  - [NOT SCORED] T002: true P3", card)
        self.assertIn("  - [NOT SCORED] T003: true P3", card)

    def test_header_accounts_for_tickets_missing_from_predictions(self):
        card = self.score([ticket("T001"), ticket("T002"), ticket("T003")],
                          [{"id": "T001", "severity": "P2", "routing": "Tier 1 Support"}])

        self.assertIn("**Tickets scored:** 1/3 (0 failed to classify, 2 not yet classified)", card)


if __name__ == "__main__":
    unittest.main()
