# Triage Scorecard

**Tickets scored:** 60/60 (0 failed to classify)

**Severity accuracy:** 45/60 (75%)

**Routing accuracy:** 52/60 (87%)


## Severity Confusion Matrix

| true \ pred | P1 | P2 | P3 | P4 |
|---|---|---|---|---|
| P1 | 12 | 0 | 0 | 0 |
| P2 | 3 | 6 | 6 | 0 |
| P3 | 0 | 4 | 9 | 2 |
| P4 | 0 | 0 | 0 | 18 |

**Under-triage (predicted less urgent than reality — the costly direction):** 8
- T012: true P2 -> predicted P3 — "Bedroom thermostat shows offline in the app, has been since yesterday. Can't adjust temp r..."
- T018: true P2 -> predicted P3 — "App keeps saying my lock is 'low battery critical' and won't let me lock remotely, though ..."
- T020: true P2 -> predicted P3 — "Access panel at the pool gate not responding to any resident fobs or the app, pool is stil..."
- T021: true P2 -> predicted P3 — "App keeps logging me out every few hours and I have to keep re-entering my password, kind ..."
- T022: true P2 -> predicted P3 — "Kitchen thermostat runs about 4 degrees colder than what I set it to, noticed this over th..."
- T050: true P3 -> predicted P4 — "App crashes every single time I try to open the energy usage tab, happens consistently on ..."
- T054: true P2 -> predicted P3 — "Community room thermostat is offline, room isn't in use this week so no rush, but flagging..."
- T055: true P3 -> predicted P4 — "Gym access panel let me in fine today but the app still shows it as 'offline' from yesterd..."

**Over-triage (predicted more urgent than reality):** 7
- T013: true P2 -> predicted P1 — "The leak sensor under my bathroom sink stopped reporting two days ago, just shows a gray i..."
- T014: true P2 -> predicted P1 — "My unit's lock keeps saying 'device unreachable' when I try to lock or unlock from the app..."
- T019: true P2 -> predicted P1 — "My unit's leak sensor by the water heater has been offline since Tuesday, tried re-pairing..."
- T023: true P3 -> predicted P2 — "My unlock schedule (auto-unlock at 8am for dog walker) hasn't been triggering the last two..."
- T030: true P3 -> predicted P2 — "Resident in 112 reported being locked out last night, our office confirmed they used the b..."
- T051: true P3 -> predicted P2 — "Push notifications for lock activity stopped coming through about a week ago, app still sh..."
- T029: true P3 -> predicted P2 — "Had an app lock issue yesterday evening, used my keypad code as backup and got in without ..."

## Confusable-Pattern Audit

Groups deliberately written to test whether the classifier applies the
nuance rules in CLAUDE.md, not just keyword matching.

- **Resolved lockout via backup code (should not stay P1)**: 1/3 correct
  - [OK] T028: true P2, predicted P2
  - [MISS] T029: true P3, predicted P2
  - [MISS] T030: true P3, predicted P2
- **False-alarm leak, confirmed dry (should downgrade to P3)**: 4/4 correct
  - [OK] T031: true P3, predicted P3
  - [OK] T032: true P3, predicted P3
  - [OK] T033: true P3, predicted P3
  - [OK] T034: true P3, predicted P3
- **Multi-unit thermostat = property-wide P1, not per-unit P2**: 2/2 correct
  - [OK] T007: true P1, predicted P1
  - [OK] T008: true P1, predicted P1
- **Unresolved >24h on safety-adjacent device = escalation override to P1**: 3/3 correct
  - [OK] T009: true P1, predicted P1
  - [OK] T010: true P1, predicted P1
  - [OK] T060: true P1, predicted P1

## Routing Misses (8)

- T006: true "Field Service / Hardware Dispatch" -> predicted "Access Control & Security" — "Front gate and lobby access panel both show offline in the dashboard as of 7am. ..."
- T012: true "Field Service / Hardware Dispatch" -> predicted "Tier 2 Escalations" — "Bedroom thermostat shows offline in the app, has been since yesterday. Can't adj..."
- T020: true "Field Service / Hardware Dispatch" -> predicted "Access Control & Security" — "Access panel at the pool gate not responding to any resident fobs or the app, po..."
- T021: true "Tier 2 Escalations" -> predicted "Product/Engineering Bug Report" — "App keeps logging me out every few hours and I have to keep re-entering my passw..."
- T022: true "Tier 2 Escalations" -> predicted "Field Service / Hardware Dispatch" — "Kitchen thermostat runs about 4 degrees colder than what I set it to, noticed th..."
- T024: true "Tier 1 Support" -> predicted "Product/Engineering Bug Report" — "App is really slow to load my thermostat settings, sometimes takes 30 seconds, b..."
- T051: true "Product/Engineering Bug Report" -> predicted "Access Control & Security" — "Push notifications for lock activity stopped coming through about a week ago, ap..."
- T058: true "Tier 1 Support" -> predicted "Access Control & Security" — "Replaced batteries in the unit 220 lock per the low-battery alert, everything wo..."
