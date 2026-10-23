#!/usr/bin/env python3
"""Classifies every ticket in data/tickets.jsonl by shelling out to the Claude Code
CLI, which auto-loads CLAUDE.md in this directory as the classification logic.
Ground-truth labels are never sent — classification is blind."""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
DATA_PATH = ROOT / "data" / "tickets.jsonl"
OUTPUT_PATH = ROOT / "predictions.jsonl"
SEVERITIES = {"P1", "P2", "P3", "P4"}

PROMPT_TEMPLATE = """Classify this support ticket per the severity taxonomy, routing \
categories, and output format defined in CLAUDE.md.

Ticket (author role: {author_role}):
\"\"\"{text}\"\"\"

Return only the JSON object described in the Output Format section. No other text."""


def classify(ticket: dict) -> dict:
    prompt = PROMPT_TEMPLATE.format(author_role=ticket["author_role"], text=ticket["text"])
    # --tools "" keeps classification blind: with tools on, the CLI could read the labels
    # in data/tickets.jsonl from cwd. It stays last since --tools takes a list of values.
    result = subprocess.run(
        ["claude", "-p", prompt, "--model", "sonnet", "--output-format", "json", "--tools", ""],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI exited {result.returncode}: {result.stderr[:500]}")
    envelope = json.loads(result.stdout)
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", envelope["result"].strip())
    prediction = json.loads(raw)
    # An answer off the CLAUDE.md output contract is a failed classification, not a
    # prediction for eval.py to score (it can't place "P1 - Critical" in the matrix).
    if not isinstance(prediction, dict) or prediction.get("severity") not in SEVERITIES \
            or not prediction.get("routing"):
        raise ValueError(f"response is not a valid severity/routing answer: {raw[:200]}")
    return prediction


def main() -> None:
    tickets = [json.loads(line) for line in DATA_PATH.open()]
    already_done = set()
    if OUTPUT_PATH.exists():
        # Only a successful prediction counts as done, so a re-run retries failures.
        # Later rows win, matching how eval.py reads the file.
        latest = {(row := json.loads(l))["id"]: row for l in OUTPUT_PATH.open()}
        already_done = {pid for pid, row in latest.items() if "error" not in row}
    remaining = [t for t in tickets if t["id"] not in already_done]
    print(f"Resuming: {len(already_done)} already done, {len(remaining)} remaining", file=sys.stderr)

    with OUTPUT_PATH.open("a") as out:
        for i, ticket in enumerate(remaining, 1):
            print(f"[{i}/{len(remaining)}] {ticket['id']}...", file=sys.stderr, end=" ")
            try:
                prediction = classify(ticket)
                out.write(json.dumps({"id": ticket["id"], **prediction}) + "\n")
                print(f"{prediction['severity']} / {prediction['routing']}", file=sys.stderr)
            except Exception as exc:
                out.write(json.dumps({"id": ticket["id"], "error": str(exc)}) + "\n")
                print(f"FAILED: {exc}", file=sys.stderr)
            out.flush()


if __name__ == "__main__":
    main()
