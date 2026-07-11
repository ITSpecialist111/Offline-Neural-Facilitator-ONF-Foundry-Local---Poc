# Six-Minute YouTube Demo — Code Blue

## Scenario

**Code Blue: Ransomware at Northstar Hospital**

Northstar is entirely fictional. The scenario is designed to demonstrate private meeting intelligence, local retrieval, defensive incident facilitation, accountable decisions, and offline model inference. It is not medical, legal, or cybersecurity advice.

The story works well on video because viewers immediately understand the stakes: a hospital's systems are unavailable, patient safety matters more than ordinary uptime, the backup is nine hours old, and the response team must make a defensible decision without sending sensitive incident details to a cloud assistant.

## What this demo proves

During one live recording, ONF should visibly:

1. replace **Untitled session** with **Code Blue: Ransomware at Northstar Hospital** from the opening sentence;
2. transcribe the speaker locally;
3. activate the ransomware, crisis, strategy, legal/compliance, and facilitator skills;
4. retrieve cited evidence from the fictional Northstar knowledge pack;
5. frame the trade-off between patient continuity and clean recovery;
6. capture one decision and three actions with owners and times;
7. answer a RAG-grounded question with Foundry Local;
8. export the result locally.

## Before recording

1. Run the application and wait for **Local service connected**.
2. Open **Capabilities** and confirm Foundry Local, Knowledge, and Transcription are ready.
3. Open **Knowledge vault**. Confirm that the curated chunk count is greater than zero.
4. Use a 1440p or 1080p browser window at 100% zoom.
5. Select dark mode for the strongest visual contrast.
6. Open a **New session**, leave the optional topic blank, and choose **Open workspace**.
7. Keep the **Guidance** tab selected.
8. Do not click **Run showcase**; this run is the live microphone demonstration.
9. Speak in short blocks and leave the indicated pauses. ONF sends complete five-second audio segments, so the pauses make each result easy to see on camera.

---

## Timed talk track

### 0:00–0:35 — Hook: why local matters

**Say to camera, before starting the microphone:**

> “Imagine it is 8:17 in the morning. A regional hospital has lost its electronic health record to ransomware. Fourteen patients are in intensive care, the latest immutable backup is nine hours old, and the response team has minutes to choose a recovery strategy. Would you send that entire conversation, the clinical context, and the incident evidence to a cloud meeting bot?”

> “This is Offline Neural Facilitator. The transcript, knowledge, reasoning, voice, and meeting record stay on this machine.”

**Point to on screen:**

- **Local service connected**;
- **Stays on this device**;
- Foundry Local, Knowledge, and Transcription readiness in the left rail.

### 0:35–1:05 — Explain the interface

**Say:**

> “The centre is the live record. The right side is deliberately separate: guidance, decisions, actions, and risks are not buried in a chatbot. The knowledge vault is local ChromaDB, and the two reasoning modes use small models through Microsoft Foundry Local.”

> “I have deliberately left the room untitled. ONF will derive the real title from the opening conversation.”

### 1:05–1:30 — Start listening and prove automatic titling

Click **Start listening**.

**Say this exact sentence first:**

> “This tabletop is called Code Blue: Ransomware at Northstar Hospital.”

**Pause for six seconds.**

**Expected result:**

- the heading changes from **Untitled session** to **Code Blue: Ransomware at Northstar Hospital**;
- **Auto-titled locally** appears beside the session identifier;
- the first transcript turn appears.

**Then say:**

> “At 08:17, ransomware took the electronic health record, shared files, and several workstations offline. Fourteen patients are in intensive care. The newest immutable backup completed at 23:00, so restoring it creates a nine-hour documentation gap. This is a critical incident, and our recovery strategy must protect patient safety and compliance.”

**Pause for eight seconds.**

**Expected result:**

- `ransomware-incident-response` activates;
- crisis, strategy, legal/compliance, and facilitator skills may also activate once each;
- the facilitator feed surfaces the incident brief or patient-safety evidence with a section-level citation.

### 1:30–2:10 — Introduce the real trade-off

**Say:**

> “The technical team can attempt the immutable restore in six to ten hours, but only after a clean-room integrity check. A clean rebuild may take eighteen to twenty-four hours. The threat actor claims a decryptor will arrive in two hours if we pay, but that is not verified recovery.”

> “Meanwhile, medication and patient identity are on downtime procedures. What does our local continuity plan say about clinical diversion, recovery order, and ransom payment?”

**Pause for eight seconds.**

**Expected result:**

- a second evidence card appears after the RAG cooldown;
- likely citations include **Diversion threshold**, **Tier One recovery order**, **Option C — Ransom payment**, or **Recommended decision frame**;
- no cloud lookup is required.

### 2:10–2:55 — Ask a grounded deep-reasoning question

Click the microphone to pause recording. Select **Deep reason**.

Type this question into **Ask the facilitator**:

> “According to the Northstar evidence, what is the safest recovery posture, what trade-off must we explicitly accept, and what facts must remain unknown?”

**While it works, say:**

> “This request uses the deeper local model. ONF sends the recent meeting context and the best-matching local evidence to Foundry Local through an OpenAI-compatible loopback endpoint. The model is on this PC; there is no Azure subscription and no per-token cloud call.”

**Expected answer themes:**

- use the earliest **verified clean** recovery, not the earliest apparent uptime;
- verify the immutable backup and rebuild identity in a clean environment;
- maintain targeted diversion until identity and medication checks pass;
- explicitly accept the nine-hour reconciliation burden;
- do not claim exfiltration, backup integrity, or the initial access path is known without evidence.

Do not worry if the exact wording differs; the citations and conclusion should remain grounded in the fictional evidence pack.

### 2:55–4:25 — Record the decision and owners

Restart **Start listening**.

**Decision — say:**

> “We have decided to reject ransom payment, keep affected segments isolated, begin the Tier One restore from the 23:00 immutable backup after integrity verification, and divert time-critical arrivals until patient identity and medication checks pass.”

**Pause for six seconds.**

**Action one — say:**

> “Action item: Priya will activate targeted clinical diversion now.”

**Pause for six seconds.**

**Action two — say:**

> “Action item: Marcus will verify backup integrity and begin the Tier One restore within thirty minutes.”

**Pause for six seconds.**

**Action three — say:**

> “Action item: Elena will notify legal counsel, the privacy officer, the cyber insurer, and incident coordination contacts by 09:00.”

**Pause for eight seconds, then stop recording.**

**Expected result:**

- one decision appears under **Decisions**;
- three actions appear under **Actions**;
- owners are Priya, Marcus, and Elena;
- due values are Now, Within thirty minutes, and By 09:00.

### 4:25–5:10 — Show the accountable record

Open **Decisions**.

**Say:**

> “The agreement is no longer a sentence hidden somewhere in a transcript. It is a canonical decision with a clear operational trade-off.”

Open **Actions**.

**Say:**

> “And these are not generic AI suggestions. They are the commitments spoken in the room, separated into named owners and time expectations.”

Open **Risks**, then **Guidance**.

**Say:**

> “The facilitator also preserves the unresolved risk and the evidence it used, so a later reviewer can see why the room made the decision.”

### 5:10–5:35 — Query the structured meeting memory

Select **Reflex** and ask:

> “What decision did we make and who owns the next steps?”

**Expected result:**

ONF returns the canonical decision followed by all three owners and actions. This answer is taken from structured session state before probabilistic generation, reducing the chance that a model changes an owner or deadline.

### 5:35–6:00 — Export and close

Choose **Export → Executive brief** or **Save session**.

**Say:**

> “The transcript, evidence, risks, decision, owners, and report are generated locally. The initial models had to be provisioned once, but this meeting can run with the network disconnected.”

> “That is the premise of Offline Neural Facilitator: move small, capable models to the sensitive conversation instead of moving the sensitive conversation to a remote model.”

## Closing line

> “Sensitive conversation in. Evidence, alignment, and accountable action out — on your hardware, under your control.”

## Troubleshooting before a take

- If the title does not update, start a fresh untitled session and repeat the exact title sentence as one short block.
- If a knowledge card has not appeared, wait fifteen seconds and say a phrase containing the relevant terms, such as “immutable backup integrity,” “clinical diversion threshold,” or “ransom payment policy.”
- If Deep reason is still warming, continue showing Decisions and Actions; structured meeting memory does not depend on the reasoning model.
- If transcription is slow on CPU, use shorter blocks and longer pauses.
- Never present the Northstar pack as real hospital policy; it is intentionally fictional and safe for demonstration.
