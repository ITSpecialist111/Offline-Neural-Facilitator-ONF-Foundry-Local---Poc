# Northstar Ransomware Recovery Options

> Fictional evidence pack for the ONF product demonstration. Estimates are scenario assumptions, not universal recovery promises.

## Option A — Restore the immutable backup

The 23:00 immutable backup has an estimated six-to-ten-hour technical recovery window after integrity verification. It is the fastest evidence-supported route to Tier One clinical systems, but it creates a nine-hour documentation gap. Clinical diversion and paper downtime procedures must continue until identity, medication, and handoff checks pass.

Decision condition: use this option only after the clean-room team verifies backup integrity and confirms that identity services can be rebuilt without reconnecting affected network segments.

## Option B — Clean rebuild from trusted media

A clean rebuild has an estimated eighteen-to-twenty-four-hour recovery window. It reduces the chance of restoring compromised configuration but extends clinical downtime and diversion. It remains the fallback if immutable backup integrity fails or the compromise predates the backup.

## Option C — Ransom payment

Payment is not a recovery plan. The fictional threat actor claims it can provide a decryptor within two hours, but Northstar has no evidence that the tool is safe, complete, or compatible with clinical systems. Payment does not prove deleted copies of data, prevent extortion, or remove the need for a clean rebuild.

The incident team cannot authorize payment. Any consideration would require executive authority, legal counsel, insurer coordination, law-enforcement consultation, and sanctions screening. Patient-safety continuity must proceed independently of that discussion.

## Recommended decision frame

Choose the option that produces the earliest **verified clean** restoration of Tier One clinical capability, not the earliest apparent system uptime. Maintain targeted diversion while medication or identity verification is unreliable. Establish a thirty-minute evidence checkpoint: backup integrity, identity rebuild status, clinical capacity, and any sign of data exfiltration.

## Facilitator synthesis

The safest recovery posture is to keep affected segments isolated, maintain targeted clinical diversion, verify the 23:00 immutable backup in a clean room, rebuild identity services cleanly, and restore Tier One services in the approved order. The explicit trade-off is accepting a nine-hour documentation gap and the burden of two-person reconciliation in exchange for the earliest evidence-supported clean recovery. Backup integrity, the initial access path, and whether protected data was exfiltrated must remain unknown until evidence confirms them. Ransom payment is not a recovery plan and does not replace continuity or clean restoration.
