package com.offlineneuralfacilitator.onf.domain.model

import java.util.UUID

const val UNTITLED_SESSION = "Untitled session"

enum class SessionStatus {
    READY,
    LIVE,
    SHOWCASE,
    PROCESSING,
}

enum class TopicSource {
    PENDING,
    MANUAL,
    CONVERSATION,
}

enum class InsightKind {
    FACILITATION,
    KNOWLEDGE,
    PACE,
    RISK,
    SKILL,
}

enum class Severity {
    LOW,
    INFO,
    MEDIUM,
    HIGH,
}

data class SessionInfo(
    val id: String,
    val status: SessionStatus = SessionStatus.READY,
    val topic: String = UNTITLED_SESSION,
    val topicSource: TopicSource = TopicSource.PENDING,
    val startedAtEpochMs: Long = System.currentTimeMillis(),
) {
    companion object {
        fun create(topic: String = UNTITLED_SESSION): SessionInfo {
            val cleanTopic = topic.trim().take(120).ifBlank { UNTITLED_SESSION }
            return SessionInfo(
                id = "ONF-${System.currentTimeMillis()}-${UUID.randomUUID().toString().take(6).uppercase()}",
                topic = cleanTopic,
                topicSource = if (cleanTopic == UNTITLED_SESSION) TopicSource.PENDING else TopicSource.MANUAL,
            )
        }
    }
}

data class TranscriptMessage(
    val id: String = UUID.randomUUID().toString(),
    val role: String,
    val speaker: String,
    val content: String,
    val timestampEpochMs: Long = System.currentTimeMillis(),
    val source: String = "live",
)

data class Insight(
    val id: String = UUID.randomUUID().toString(),
    val kind: InsightKind,
    val title: String,
    val text: String,
    val severity: Severity = Severity.INFO,
    val citation: String? = null,
    val source: String = "facilitator",
    val timestampEpochMs: Long = System.currentTimeMillis(),
)

data class ActionItem(
    val id: String = UUID.randomUUID().toString(),
    val text: String,
    val owner: String = "Unassigned",
    val due: String = "Not set",
    val status: String = "open",
    val timestampEpochMs: Long = System.currentTimeMillis(),
)

data class Decision(
    val id: String = UUID.randomUUID().toString(),
    val text: String,
    val rationale: String = "",
    val timestampEpochMs: Long = System.currentTimeMillis(),
)

data class SessionMetrics(
    val durationSeconds: Long = 0,
    val wordCount: Int = 0,
    val turnCount: Int = 0,
    val insightCount: Int = 0,
    val actionCount: Int = 0,
    val riskCount: Int = 0,
    val alignmentScore: Int = 72,
)

data class OnfState(
    val session: SessionInfo = SessionInfo.create(),
    val transcript: List<TranscriptMessage> = emptyList(),
    val insights: List<Insight> = emptyList(),
    val decisions: List<Decision> = emptyList(),
    val actions: List<ActionItem> = emptyList(),
    val risks: List<Insight> = emptyList(),
    val activeSkills: Set<String> = emptySet(),
    val metrics: SessionMetrics = SessionMetrics(),
)

data class ActionDraft(
    val text: String,
    val owner: String,
    val due: String,
)
