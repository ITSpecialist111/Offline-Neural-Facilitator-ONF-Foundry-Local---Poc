# Commander's Intent

## Mission

Make sensitive meetings produce **clear, evidence-grounded and accountable outcomes without sending the conversation to the cloud**.

ONF is not another chat window. It is a quiet meeting operating layer that captures what was said, notices when the room is stuck, recalls relevant local evidence, records the decision, assigns the next move and produces a durable local record.

## Desired end state

At the end of a successful ONF session:

1. Participants can see an accurate, readable record of the discussion.
2. The facilitator has intervened only where it improved pace, clarity, evidence or alignment.
3. Every material decision is explicit.
4. Every next action has an owner and a time expectation.
5. Relevant claims can be traced to a local source.
6. The complete record can be saved or exported without cloud infrastructure.

The product loop is:

> **Capture → understand → intervene → decide → export**

## Primary user

A facilitator, delivery lead, incident commander, legal/compliance professional or strategy lead handling a conversation that is too sensitive, too consequential or too time-critical for a cloud meeting assistant.

## Non-negotiable constraints

- **Local-first:** inference, transcription, retrieval, session state and exports run on the user's machine.
- **Honest capability state:** the interface must distinguish ready, loading and unavailable capabilities. It must never imply that a model is running when it is not.
- **Graceful degradation:** the workspace, deterministic showcase, structured outcomes and exports remain usable while heavyweight models warm or are unavailable.
- **Quiet intervention:** do not flood the room with generic AI commentary. Surface a small number of timely, explainable interventions.
- **Evidence before eloquence:** cited local context is more valuable than an impressive unsupported answer.
- **Human authority:** ONF frames choices and records commitments; it does not make consequential decisions for the group.

## Showcase proof

A viewer should understand the product in under three minutes:

1. The header visibly confirms local connectivity and on-device privacy.
2. **Run showcase** begins a fictional hospital ransomware decision room.
3. The transcript reveals disagreement.
4. ONF separates patient continuity, clean recovery, and extortion into explicit decision tracks.
5. Cited local evidence frames diversion and immutable-backup recovery.
6. One recovery decision and three owned actions appear in dedicated views.
7. The meeting is exported locally.

## Not the mission

- A general-purpose assistant for unrelated questions.
- An autonomous meeting chair that constantly interrupts.
- A surveillance or emotion-scoring system.
- A cloud collaboration platform.
- A claim of production-grade speaker identity before real diarization is implemented and validated.

When implementation choices conflict, preserve the mission, constraints and desired end state above. Features are optional; the commander's intent is not.