package com.offlineneuralfacilitator.onf.domain

import android.os.SystemClock
import com.offlineneuralfacilitator.onf.ai.EnginePhase
import com.offlineneuralfacilitator.onf.ai.LocalLlmEngine
import com.offlineneuralfacilitator.onf.data.OnfRepository
import com.offlineneuralfacilitator.onf.domain.FacilitationRules.recordCase
import com.offlineneuralfacilitator.onf.domain.model.ActionItem
import com.offlineneuralfacilitator.onf.domain.model.Decision
import com.offlineneuralfacilitator.onf.domain.model.Insight
import com.offlineneuralfacilitator.onf.domain.model.InsightKind
import com.offlineneuralfacilitator.onf.domain.model.OnfState
import com.offlineneuralfacilitator.onf.domain.model.SessionStatus
import com.offlineneuralfacilitator.onf.domain.model.Severity
import com.offlineneuralfacilitator.onf.domain.model.TranscriptMessage
import com.offlineneuralfacilitator.onf.domain.model.UNTITLED_SESSION
import com.offlineneuralfacilitator.onf.skills.SkillEngine
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

internal class Facilitator(
    private val repository: OnfRepository,
    private val skills: SkillEngine,
    private val llm: LocalLlmEngine,
) {
    val state: StateFlow<OnfState> = repository.state
    private val analysisMutex = Mutex()
    private var lastKnowledgeSignature: String? = null
    private var lastKnowledgeAt = 0L

    suspend fun initialize() = repository.initialize()

    suspend fun newSession(topic: String = UNTITLED_SESSION) {
        analysisMutex.withLock {
            lastKnowledgeSignature = null
            lastKnowledgeAt = 0L
            repository.newSession(topic)
        }
    }

    suspend fun addParticipantText(
        text: String,
        speaker: String = "Speaker",
        source: String = "manual",
        analyze: Boolean = true,
    ) = analysisMutex.withLock {
        val clean = FacilitationRules.normalize(text)
        if (clean.length < 2) return@withLock
        repository.addTranscript(
            TranscriptMessage(
                role = "participant",
                speaker = speaker.ifBlank { "Speaker" },
                content = clean,
                source = source,
            ),
        )
        maybeTitle(clean)
        if (analyze) analyze(clean)
    }

    suspend fun ask(query: String): String = analysisMutex.withLock {
        val clean = FacilitationRules.normalize(query)
        if (clean.isBlank()) return@withLock "Enter a question for the facilitator."
        repository.addTranscript(
            TranscriptMessage(role = "user", speaker = "You", content = clean, source = "chat"),
        )
        maybeTitle(clean)
        val skillMatch = skills.match(clean)
        activateNewSkills(skillMatch.names)
        val stateBeforeAnswer = state.value
        val structured = structuredAnswer(clean, stateBeforeAnswer)
        val knowledge = repository.searchKnowledge(clean, 3).filter { it.relevance >= KNOWLEDGE_THRESHOLD }
        val context = knowledge.joinToString("\n\n") { match ->
            "[Source: ${match.chunk.source} · ${match.chunk.section}] ${match.chunk.text}"
        }
        val meeting = stateBeforeAnswer.transcript.takeLast(10).joinToString("\n") {
            "${it.speaker}: ${it.content}"
        }
        val response = structured ?: if (llm.status.value.phase == EnginePhase.READY) {
            runCatching {
                llm.generate(
                    systemInstruction = SYSTEM_INSTRUCTION + skillMatch.instructions,
                    prompt = """
                        Local knowledge:
                        ${context.ifBlank { "None" }}

                        Meeting so far:
                        $meeting

                        Question: $clean
                    """.trimIndent(),
                )
            }.getOrNull()
        } else {
            null
        } ?: fallback(clean, stateBeforeAnswer)

        repository.addTranscript(
            TranscriptMessage(role = "assistant", speaker = "Facilitator", content = response, source = "local"),
        )
        response
    }

    suspend fun runShowcase() = analysisMutex.withLock {
        repository.newSession("Code Blue: Ransomware at Northstar Hospital")
        repository.setStatus(SessionStatus.SHOWCASE)
        val turns = listOf(
            "Priya Shah" to "At 08:17 a ransomware incident took the EHR offline. Fourteen ICU patients are on the ward, and our newest immutable backup is nine hours old.",
            "Marcus Reed" to "I disagree with restoring immediately. If identity services are not clean, a fast reconnection is too risky. But continued downtime also threatens patient safety.",
            "Elena Torres" to "The local continuity card says we divert time-critical arrivals when identity or medication verification is unreliable for thirty minutes. The recovery matrix favors the earliest verified clean restore.",
        )
        for ((speaker, text) in turns) {
            repository.addTranscript(TranscriptMessage(role = "participant", speaker = speaker, content = text, source = "showcase"))
            delay(250)
        }
        repository.addInsight(
            Insight(
                kind = InsightKind.RISK,
                title = "Alignment gap detected",
                text = "Separate patient continuity, clean restoration, and extortion into explicit decision tracks.",
                severity = Severity.HIGH,
            ),
        )
        repository.addInsight(
            Insight(
                kind = InsightKind.KNOWLEDGE,
                title = "Relevant continuity evidence",
                text = "Targeted diversion begins when identity or medication verification is unreliable for thirty continuous minutes. Restore only after clean-room integrity verification.",
                citation = "Northstar Clinical Continuity Card · Diversion threshold",
                source = "knowledge vault",
            ),
        )
        repository.addInsight(
            Insight(
                kind = InsightKind.SKILL,
                title = "Ransomware response activated",
                text = "Patient safety, clean recovery evidence, decision authority, and a timed checkpoint now shape guidance.",
                source = "skills",
            ),
        )
        repository.addDecision(
            Decision(
                text = "Reject ransom payment, begin the verified Tier One restore, and divert time-critical arrivals until identity and medication checks pass",
                rationale = "Prioritizes patient safety and the earliest evidence-supported clean recovery.",
            ),
        )
        repository.addAction(ActionItem(text = "Activate targeted clinical diversion", owner = "Priya", due = "Now"))
        repository.addAction(ActionItem(text = "Verify backup integrity and start the Tier One restore", owner = "Marcus", due = "Within thirty minutes"))
        repository.addAction(ActionItem(text = "Notify legal counsel, privacy, insurer, and incident coordination", owner = "Elena", due = "By 09:00"))
        repository.addInsight(
            Insight(
                kind = InsightKind.FACILITATION,
                title = "Decision frame clarified",
                text = "The team separated patient continuity from technical recovery, rejected an unverified shortcut, assigned three owners, and set a thirty-minute evidence checkpoint.",
                severity = Severity.LOW,
            ),
        )
        repository.setStatus(SessionStatus.READY)
    }

    suspend fun importKnowledge(filename: String, content: String): Int =
        repository.importKnowledge(filename, content)

    fun knowledgeCount(): Int = repository.knowledgeCount()

    private suspend fun maybeTitle(text: String) {
        if (state.value.session.topic != UNTITLED_SESSION) return
        val participantTurns = state.value.transcript.count { it.role == "participant" || it.role == "user" }
        val title = FacilitationRules.explicitTitle(text)
            ?: if (participantTurns >= 2) FacilitationRules.fallbackTitle(text) else null
        if (!title.isNullOrBlank()) repository.setTopic(title)
    }

    private suspend fun analyze(text: String) {
        val skillMatch = skills.match(text)
        activateNewSkills(skillMatch.names)

        FacilitationRules.actions(text).forEach { draft ->
            repository.addAction(ActionItem(text = draft.text, owner = draft.owner, due = draft.due))
        }
        FacilitationRules.decision(text)?.let { repository.addDecision(Decision(text = it)) }

        val current = state.value
        val hasAlignmentAlert = current.risks.any { it.title == "Alignment gap detected" }
        if (!hasAlignmentAlert && FacilitationRules.hasAlignmentGap(current.transcript)) {
            repository.addInsight(
                Insight(
                    kind = InsightKind.RISK,
                    title = "Alignment gap detected",
                    text = "Two positions are diverging. Name the shared constraint before evaluating options.",
                    severity = Severity.HIGH,
                ),
            )
        }
        if (FacilitationRules.isHighDensity(text)) {
            repository.addInsight(
                Insight(
                    kind = InsightKind.PACE,
                    title = "High information density",
                    text = "A large amount of context landed at once. Summarize the constraint before moving to a decision.",
                    severity = Severity.MEDIUM,
                ),
            )
        }

        repository.searchKnowledge(text, 1).firstOrNull()?.takeIf { match ->
            match.relevance >= KNOWLEDGE_THRESHOLD &&
                match.chunk.id.toString() != lastKnowledgeSignature &&
                SystemClock.elapsedRealtime() - lastKnowledgeAt >= KNOWLEDGE_COOLDOWN_MS
        }?.let { match ->
            lastKnowledgeSignature = match.chunk.id.toString()
            lastKnowledgeAt = SystemClock.elapsedRealtime()
            repository.addInsight(
                Insight(
                    kind = InsightKind.KNOWLEDGE,
                    title = "Relevant local evidence",
                    text = match.chunk.text.take(360),
                    citation = "${match.chunk.source} · ${match.chunk.section}",
                    source = "knowledge vault",
                ),
            )
        }
    }

    private suspend fun activateNewSkills(names: List<String>) {
        val newSkills = names.filterNot(state.value.activeSkills::contains)
        if (newSkills.isEmpty()) return
        repository.activateSkills(newSkills)
        newSkills.forEach { name ->
            repository.addInsight(
                Insight(
                    kind = InsightKind.SKILL,
                    title = "Specialist skill activated",
                    text = "$name is now shaping facilitator guidance.",
                    source = "skills",
                ),
            )
        }
    }

    private fun structuredAnswer(query: String, snapshot: OnfState): String? {
        val lower = query.lowercase()
        val parts = mutableListOf<String>()
        if (listOf("decision", "decide", "agreed").any(lower::contains) && snapshot.decisions.isNotEmpty()) {
            parts += "The recorded decision is: ${snapshot.decisions.joinToString("; ") { it.text }}."
        }
        if (listOf("action", "owner", "next step", "who").any(lower::contains) && snapshot.actions.isNotEmpty()) {
            val selected = if (listOf("single", "most important", "first").any(lower::contains)) snapshot.actions.take(1) else snapshot.actions
            parts += "The owned next steps are: ${selected.joinToString("; ") { "${it.owner} — ${it.text} (${it.due})" }}."
        }
        if (listOf("risk", "blocker", "concern").any(lower::contains) && snapshot.risks.isNotEmpty()) {
            parts += "The principal recorded risk is: ${snapshot.risks.joinToString("; ") { it.text }}."
        }
        return parts.joinToString(" ").takeIf(String::isNotBlank)
    }

    private fun fallback(query: String, snapshot: OnfState): String {
        if (listOf("summary", "summarize", "recap").any(query.lowercase()::contains)) {
            val decisions = snapshot.decisions.joinToString("; ") { it.text }.ifBlank { "No explicit decision yet" }
            val actions = snapshot.actions.joinToString("; ") { "${it.owner}: ${it.text}" }.ifBlank { "No owned action yet" }
            return "The session covers ${snapshot.session.topic}. Decisions: $decisions. Next actions: $actions."
        }
        return "I can retrieve recorded decisions, actions, risks, and local evidence now. Import a Gemma 4 .litertlm model to enable open-ended private reasoning over this session."
    }

    companion object {
        private const val KNOWLEDGE_THRESHOLD = 0.24f
        private const val KNOWLEDGE_COOLDOWN_MS = 15_000L
        private const val SYSTEM_INSTRUCTION =
            "You are ONF, a concise and neutral meeting facilitator. Clarify evidence, surface trade-offs, record decisions, and leave every next step with an owner. Ground claims only in supplied local context. Never claim an external lookup. Do not reveal chain-of-thought. Keep the final answer under 160 words.\n\n"
    }
}
