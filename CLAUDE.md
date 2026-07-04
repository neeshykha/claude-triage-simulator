# Ticket Triage Classification Logic

This file is the actual instruction set used by `triage.py` to classify each ticket. It is not documentation written after the fact — it is loaded into the classification prompt at runtime. Treat changes to this file as changes to the classifier's behavior, not just its description.

## Domain

Support tickets for an IoT/smart-home platform serving multifamily residential properties (apartment communities). Devices in scope: smart locks, thermostats, leak/water sensors, community area access panels, in-unit sensors, and the resident-facing mobile app. Ticket authors are a mix of residents, property managers, and on-site maintenance staff.

## Severity Taxonomy

Classify into exactly one of four levels. Work through the checks in order — the first one that applies sets the severity, then later checks can only push it up, never down.

**P1 — Critical**
Any of: active safety or security exposure (a lock is unresponsive and someone is locked out or a unit is unsecured), active property damage in progress (a leak sensor should be alerting but isn't, or a leak alert with no one dispatched), or an outage affecting multiple units or the whole property with no workaround.

**P2 — High**
A single resident or unit is fully blocked from a core function (device totally offline, thermostat stuck at an extreme setting, lock will not respond to any input) but there is no active safety/damage exposure and no property-wide scope.

**P3 — Medium**
Degraded but functional. A workaround exists (manual override, a second working device, delayed-but-eventual sync) or the issue is annoying but not blocking (schedule drift, slow app refresh, one sensor down out of several).

**P4 — Low**
No functional impact: how-to questions, account/app UI confusion, feature requests, cosmetic issues.

**Escalation override:** if a ticket describes a device category that is safety-adjacent (locks, leak sensors) AND the resident reports it has been unresolved for more than 24 hours, bump the severity one level regardless of the above — unresolved time compounds risk for these categories specifically. This does not apply to thermostats or app/billing issues.

## Routing Categories

Route to exactly one team:

- **Tier 1 Support** — how-to questions, account/app navigation, anything a resident could resolve with guidance
- **Tier 2 Escalations** — technical issues beyond a basic walkthrough, but not requiring a truck roll or a security determination
- **Field Service / Hardware Dispatch** — a physical device needs replacement, repair, or in-person diagnosis
- **Access Control & Security** — anything involving locks, entry systems, or unit access/security, regardless of severity
- **Environmental Monitoring** — leak, humidity, or temperature sensor issues tied to property damage risk
- **Billing & Account Management** — charges, subscriptions, account ownership/transfer
- **Product/Engineering Bug Report** — a software defect not tied to one specific device (app crash, sync failure across many users, dashboard error)

**Routing tie-breaks:** if a ticket touches both a device category (lock, sensor) and looks like a software bug, route by whichever the ticket text more directly blames — "the app won't let me" routes to Product/Engineering, "the lock won't unlock" routes to Access Control & Security, even if the underlying cause might be the same firmware update.

## Known Confusable Patterns

These are the cases where the naive read gets it wrong — worth extra attention:

- **Leak sensor "false alarm" tickets** often use urgent language ("water everywhere," "emergency") but if the resident confirms no actual damage occurred and the sensor is now reading normally, this is a P3 sensor-accuracy issue, not a P1 — the risk already passed.
- **"Locked out" tickets** are P1 only if the person is currently locked out right now. A ticket describing a lockout that already got resolved via a keypad backup code is P2 at most — document the gap, do not treat as ongoing.
- **Multi-unit thermostat complaints** in the same building within a short window usually indicate a shared HVAC controller issue, not four separate P2s — if the ticket references "several units" or "the whole floor," treat as P1 property-wide scope even though the device itself is a thermostat (normally a P2-max category).
- **Property manager tickets** tend to under-describe urgency in favor of formal language ("please advise") — do not let a calm tone downgrade severity if the underlying facts (active lockout, active leak) meet the P1 bar.

## Output Format

For each ticket, return strict JSON with no other text:

```json
{"severity": "P1", "routing": "Access Control & Security", "reasoning": "one sentence"}
```
