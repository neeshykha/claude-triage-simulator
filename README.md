# Claude Triage Simulator

An AI ticket triage classifier for IoT/smart-home support, built on [Claude Code](https://claude.ai/code), with a scoring harness that measures whether it actually works instead of just demoing it. The scenario: a support ticket comes in, and someone (or something) has to decide how urgent it is and who should handle it — a decision real support teams make dozens of times a day, and one that's easy to get either dangerously wrong (missing a real emergency) or expensively wrong (dispatching a truck roll for a how-to question).

The tickets are synthetic, but the rules aren't — the severity taxonomy, routing categories, and "known confusable patterns" in `CLAUDE.md` are drawn directly from patterns in multifamily IoT support operations, not from public ticket data (see note on the dataset below).

---

## How It Works

**`CLAUDE.md` — the instruction layer**
The actual classification logic: a 4-level severity taxonomy (P1–P4), 7 routing categories, an escalation-override rule for unresolved safety-adjacent issues, and four "known confusable patterns" — cases where a naive read of the ticket text gets the answer wrong (a leak sensor false alarm that *sounds* urgent, a resolved lockout that shouldn't stay P1, a multi-unit thermostat failure that's actually property-wide). Claude Code loads this file automatically for every classification call — it's the runtime prompt, not documentation written after the fact.

**`triage.py` and `eval.py` — the automation layer**
`triage.py` shells out to the Claude Code CLI once per ticket, blind — it never sees the ground-truth label, only the ticket text and author role. `eval.py` scores every prediction against the labeled dataset and produces a scorecard: overall accuracy, a full severity confusion matrix, an under-triage vs. over-triage breakdown (missing a real emergency and over-flagging a routine ticket are not the same cost), and a pass/fail audit of the trap tickets specifically — three of the four confusable patterns, plus the escalation override.

```
triage.py reads data/tickets.jsonl
→ For each ticket, calls the claude CLI (CLAUDE.md drives the classification)
→ Writes predictions.jsonl
→ eval.py compares predictions to ground truth
→ results/scorecard.md
```

---

## Results (last run)

60 tickets, 60 scored, 0 classification failures.

| Metric | Result |
|---|---|
| Severity accuracy | 75% (45/60) |
| Routing accuracy | 87% (52/60) |
| P1 tickets caught | 12/12 (100%) |
| Under-triage (missed urgency) | 8 |
| Over-triage (flagged too high) | 7 |

The strongest result isn't the headline accuracy — it's that **every P1 was caught**, and no miss jumped more than one severity band (nothing that was actually critical got waved through as routine). The clearest weak spot among the trap groups: tickets describing a lockout that was already resolved via a backup code. The classifier caught 1 of 3 — it moved all three off P1, but stopped at P2 on the two labeled P3 (T029, T030). `CLAUDE.md` only says this pattern is "P2 at most," so the rule itself never draws that P2/P3 line. That's a legible, specific failure mode, not a vague accuracy gap, which is exactly what an eval harness is supposed to surface.

Full breakdown, confusion matrix, and per-ticket misses: [`results/scorecard.md`](results/scorecard.md), or the [report page](https://neeshykha.github.io/claude-triage-simulator/) for the same results with the ticket text behind each miss.

---

## Repo Structure

```
CLAUDE.md                  # The classification logic — start here
data/tickets.jsonl          # 60 labeled synthetic tickets (id, text, author_role, true_severity, true_routing)
triage.py                   # Blind classification via the Claude Code CLI
eval.py                     # Scoring harness: accuracy, confusion matrix, confusable-pattern audit
tests.py                    # Regression tests for triage.py and eval.py (python3 -m unittest)
results/scorecard.md        # Output of the last real run
docs/index.html             # Report page rendering the scorecard (served via GitHub Pages)
```

`predictions.jsonl` is generated locally and gitignored — regenerate it with `triage.py`.

---

## Setup

```bash
git clone https://github.com/neeshykha/claude-triage-simulator
cd claude-triage-simulator

# Requires the Claude Code CLI, authenticated
python3 triage.py   # classifies all 60 tickets, ~1-2 min
python3 eval.py     # scores predictions, writes results/scorecard.md
```

`triage.py` is resumable — if interrupted, re-running it skips tickets already classified in `predictions.jsonl` and retries any that failed.

---

## On the Dataset

The 60 tickets are synthetic, written to mirror real patterns from multifamily IoT support operations (severity distribution, routing categories, and the specific edge cases in "Known Confusable Patterns") without using any actual customer or company data. No production ticket content — from this project or any employer — appears anywhere in this repo.

---

## Tech Stack

- **Claude Code** — classification logic and execution
- **Python (stdlib only)** — dataset handling, subprocess orchestration, scoring
