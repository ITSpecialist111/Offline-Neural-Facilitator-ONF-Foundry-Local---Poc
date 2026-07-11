# Northstar Hospital Code Blue Tabletop — Incident Brief

> Fictional evidence pack for the ONF product demonstration. It is not medical, legal, or cybersecurity advice.

## Situation at 08:17

Northstar Community Hospital is a fictional 180-bed regional hospital. At 08:17, monitoring detected a ransomware incident affecting the electronic health record (EHR), shared file services, and several administrative workstations. The hospital has isolated its external connection, but the scope inside the clinical network is not yet confirmed.

Fourteen patients are in intensive care. The emergency department has six time-critical patients under assessment. Medication administration, patient identity checks, laboratory orders, and imaging requests are operating on downtime procedures. No patient harm has been reported.

The newest immutable backup completed at 23:00, nine hours before detection. Backup integrity has not yet been verified. Restoring it could create a nine-hour documentation gap that must be reconciled from paper records and local device logs.

## Decision required by 08:45

The incident command team must select a recovery posture before 08:45. The decision must protect patient safety, preserve forensic evidence, avoid spreading the incident, and define who can authorize each recovery step.

The decision is not simply whether to restore or pay. It must also establish the clinical diversion threshold, the order in which Tier One services return, the accepted documentation gap, and the next evidence checkpoint.

## Facts not yet known

The initial access path is unknown. The team does not yet know whether protected data was copied before encryption, whether every backup tier is clean, or whether identity infrastructure is affected. These uncertainties must be stated rather than guessed.
