#!/usr/bin/env python3
"""Scores triage.py's predictions against ground truth. Severity misses are split
into under-triage (predicted less urgent than reality — the costly direction) and
over-triage, since those carry different operational risk."""

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent
SEVERITY_ORDER = ["P1", "P2", "P3", "P4"]

# Tickets deliberately written as known-confusable patterns (see CLAUDE.md).
# Each entry: (ids, label) — used to report whether the classifier caught the trap.
CONFUSABLE_GROUPS = [
    (["T028", "T029", "T030"], "Resolved lockout via backup code (should not stay P1)"),
    (["T031", "T032", "T033", "T034"], "False-alarm leak, confirmed dry (should downgrade to P3)"),
    (["T007", "T008"], "Multi-unit thermostat = property-wide P1, not per-unit P2"),
    (["T009", "T010", "T060"], "Unresolved >24h on safety-adjacent device = escalation override to P1"),
]


def load_jsonl(path: Path) -> dict:
    return {json.loads(l)["id"]: json.loads(l) for l in path.open()}


def ratio(k: int, n: int) -> str:
    return f"{k}/{n} ({k/n:.0%})" if n else f"{k}/{n} (n/a)"


def main() -> None:
    tickets = load_jsonl(ROOT / "data" / "tickets.jsonl")
    predictions = load_jsonl(ROOT / "predictions.jsonl")

    lines = []
    lines.append("# Triage Scorecard\n")

    errors = [pid for pid, p in predictions.items() if "error" in p]
    scored = {pid: p for pid, p in predictions.items() if "error" not in p}
    n = len(scored)

    sev_correct = sum(1 for pid, p in scored.items() if p["severity"] == tickets[pid]["true_severity"])
    route_correct = sum(1 for pid, p in scored.items() if p["routing"] == tickets[pid]["true_routing"])

    missing = [pid for pid in tickets if pid not in predictions]
    not_run = f", {len(missing)} not yet classified" if missing else ""
    lines.append(f"**Tickets scored:** {n}/{len(tickets)} ({len(errors)} failed to classify{not_run})\n")
    lines.append(f"**Severity accuracy:** {ratio(sev_correct, n)}\n")
    lines.append(f"**Routing accuracy:** {ratio(route_correct, n)}\n")

    # Confusion matrix for severity
    lines.append("\n## Severity Confusion Matrix\n")
    header = "| true \\ pred | " + " | ".join(SEVERITY_ORDER) + " |"
    lines.append(header)
    lines.append("|" + "---|" * (len(SEVERITY_ORDER) + 1))
    matrix = {t: Counter() for t in SEVERITY_ORDER}
    for pid, p in scored.items():
        matrix[tickets[pid]["true_severity"]][p["severity"]] += 1
    for t in SEVERITY_ORDER:
        row = " | ".join(str(matrix[t][pred]) for pred in SEVERITY_ORDER)
        lines.append(f"| {t} | {row} |")

    # Under- vs over-triage
    under, over = [], []
    for pid, p in scored.items():
        true_idx = SEVERITY_ORDER.index(tickets[pid]["true_severity"])
        pred_idx = SEVERITY_ORDER.index(p["severity"])
        if pred_idx > true_idx:
            under.append((pid, tickets[pid]["true_severity"], p["severity"]))
        elif pred_idx < true_idx:
            over.append((pid, tickets[pid]["true_severity"], p["severity"]))

    lines.append(f"\n**Under-triage (predicted less urgent than reality — the costly direction):** {len(under)}")
    for pid, true_s, pred_s in under:
        lines.append(f"- {pid}: true {true_s} -> predicted {pred_s} — \"{tickets[pid]['text'][:90]}...\"")
    lines.append(f"\n**Over-triage (predicted more urgent than reality):** {len(over)}")
    for pid, true_s, pred_s in over:
        lines.append(f"- {pid}: true {true_s} -> predicted {pred_s} — \"{tickets[pid]['text'][:90]}...\"")

    # Confusable pattern audit
    lines.append("\n## Confusable-Pattern Audit\n")
    lines.append("Groups deliberately written to test whether the classifier applies the")
    lines.append("nuance rules in CLAUDE.md, not just keyword matching.\n")
    for ids, label in CONFUSABLE_GROUPS:
        # Same denominator as the accuracy lines: failed or never-classified tickets
        # are reported as not scored rather than counted as misses.
        group_scored = [pid for pid in ids if pid in scored]
        hits = sum(1 for pid in group_scored if scored[pid]["severity"] == tickets[pid]["true_severity"])
        unscored = len(ids) - len(group_scored)
        suffix = f" ({unscored} not scored)" if unscored else ""
        lines.append(f"- **{label}**: {hits}/{len(group_scored)} correct{suffix}")
        for pid in ids:
            if pid not in scored:
                lines.append(f"  - [NOT SCORED] {pid}: true {tickets[pid]['true_severity']}")
                continue
            mark = "OK" if scored[pid]["severity"] == tickets[pid]["true_severity"] else "MISS"
            lines.append(f"  - [{mark}] {pid}: true {tickets[pid]['true_severity']}, predicted {scored[pid]['severity']}")

    # Routing misses
    routing_misses = [
        (pid, tickets[pid]["true_routing"], p["routing"])
        for pid, p in scored.items() if p["routing"] != tickets[pid]["true_routing"]
    ]
    lines.append(f"\n## Routing Misses ({len(routing_misses)})\n")
    for pid, true_r, pred_r in routing_misses:
        lines.append(f"- {pid}: true \"{true_r}\" -> predicted \"{pred_r}\" — \"{tickets[pid]['text'][:80]}...\"")

    if errors:
        lines.append(f"\n## Classification Failures ({len(errors)})\n")
        for pid in errors:
            lines.append(f"- {pid}: {predictions[pid]['error'][:200]}")

    report = "\n".join(lines) + "\n"
    out_path = ROOT / "results" / "scorecard.md"
    out_path.write_text(report)
    print(report)


if __name__ == "__main__":
    main()
