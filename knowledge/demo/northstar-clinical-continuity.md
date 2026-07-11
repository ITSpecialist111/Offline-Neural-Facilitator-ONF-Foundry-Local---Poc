# Northstar Clinical Continuity Card

> Fictional evidence pack for the ONF product demonstration. Local policy always overrides this scenario.

## Patient-safety priorities

Northstar's continuity rule is safety before speed. During a digital outage, the incident commander must preserve reliable patient identity, medication administration, critical laboratory results, clinical handoff, and emergency communication before restoring convenience or revenue systems.

Teams must not reconnect an unverified service merely because it appears operational. A clean, slower recovery is preferred to a fast reconnection that could reintroduce the incident.

## Diversion threshold

Northstar activates targeted clinical diversion when either patient identity or medication verification cannot be performed reliably for thirty continuous minutes, or when ICU and emergency handoffs cannot be reconciled by two qualified staff members.

Diversion applies first to new time-critical arrivals. Existing patients remain under the hospital's continuity procedures unless the clinical lead determines that safe care can no longer be maintained.

## Tier One recovery order

The approved recovery sequence is:

1. identity and privileged access services in a clean environment;
2. medication administration and pharmacy verification;
3. critical laboratory ordering and results;
4. imaging worklists and reports;
5. read-only EHR access followed by controlled write access;
6. scheduling, billing, and other administrative systems.

Each stage requires an integrity check and a named clinical acceptance owner before the next stage begins.

## Documentation reconciliation

If Northstar restores the 23:00 immutable backup, the nine-hour data gap must be reconciled from signed paper records, medication device logs, laboratory instruments, and departmental downtime forms. Two-person verification is required for medication and identity corrections. The reconciliation record becomes part of the incident evidence package.
