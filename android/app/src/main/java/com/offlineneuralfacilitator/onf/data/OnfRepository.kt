package com.offlineneuralfacilitator.onf.data

import android.content.Context
import com.offlineneuralfacilitator.onf.domain.FacilitationRules
import com.offlineneuralfacilitator.onf.domain.model.ActionItem
import com.offlineneuralfacilitator.onf.domain.model.Decision
import com.offlineneuralfacilitator.onf.domain.model.Insight
import com.offlineneuralfacilitator.onf.domain.model.InsightKind
import com.offlineneuralfacilitator.onf.domain.model.OnfState
import com.offlineneuralfacilitator.onf.domain.model.SessionInfo
import com.offlineneuralfacilitator.onf.domain.model.SessionStatus
import com.offlineneuralfacilitator.onf.domain.model.TranscriptMessage
import com.offlineneuralfacilitator.onf.rag.KnowledgeMatch
import com.offlineneuralfacilitator.onf.rag.RagRanker
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import java.util.UUID

internal class OnfRepository(
    private val context: Context,
    private val database: OnfDatabase = OnfDatabase(context),
    private val ranker: RagRanker = RagRanker(),
) {
    private val mutex = Mutex()
    private val _state = MutableStateFlow(OnfState())
    val state: StateFlow<OnfState> = _state.asStateFlow()

    suspend fun initialize() = withContext(Dispatchers.IO) {
        mutex.withLock {
            val restored = database.latest() ?: OnfState()
            _state.value = restored.copy(metrics = FacilitationRules.metrics(restored))
            database.save(_state.value)
            if (database.knowledgeCount() == 0) seedBundledKnowledge()
        }
    }

    suspend fun newSession(topic: String) = update {
        OnfState(session = SessionInfo.create(topic))
    }

    suspend fun setStatus(status: SessionStatus) = update { current ->
        current.copy(session = current.session.copy(status = status))
    }

    suspend fun setTopic(topic: String) = update { current ->
        current.copy(
            session = current.session.copy(
                topic = topic.trim().take(120),
                topicSource = com.offlineneuralfacilitator.onf.domain.model.TopicSource.CONVERSATION,
            ),
        )
    }

    suspend fun addTranscript(message: TranscriptMessage) = update { current ->
        current.copy(transcript = current.transcript + message)
    }

    suspend fun addInsight(insight: Insight) = update { current ->
        current.copy(
            insights = current.insights + insight,
            risks = if (insight.kind == InsightKind.RISK) current.risks + insight else current.risks,
        )
    }

    suspend fun addAction(action: ActionItem) = update { current ->
        if (current.actions.any { it.text.equals(action.text, ignoreCase = true) }) current
        else current.copy(actions = current.actions + action)
    }

    suspend fun addDecision(decision: Decision) = update { current ->
        if (current.decisions.any { it.text.equals(decision.text, ignoreCase = true) }) current
        else current.copy(decisions = current.decisions + decision)
    }

    suspend fun activateSkills(names: Collection<String>) = update { current ->
        current.copy(activeSkills = current.activeSkills + names)
    }

    suspend fun searchKnowledge(query: String, limit: Int = 3): List<KnowledgeMatch> = withContext(Dispatchers.IO) {
        ranker.search(query, database.knowledge(), limit)
    }

    suspend fun importKnowledge(filename: String, content: String): Int = withContext(Dispatchers.IO) {
        val title = filename.substringBeforeLast('.').replace('-', ' ').replace('_', ' ')
            .split(' ').joinToString(" ") { it.replaceFirstChar(Char::uppercase) }
        val sections = MarkdownSections.parse(content, title)
            .ifEmpty { listOf(MarkdownSection(title, "Overview", content)) }
        database.replaceKnowledge("manual:${UUID.randomUUID()}", sections, curated = false)
    }

    fun knowledgeCount(): Int = database.knowledgeCount()

    private suspend fun update(transform: (OnfState) -> OnfState) = withContext(Dispatchers.IO) {
        mutex.withLock {
            val changed = transform(_state.value)
            val measured = changed.copy(metrics = FacilitationRules.metrics(changed))
            database.save(measured)
            _state.value = measured
        }
    }

    private fun seedBundledKnowledge() {
        context.assets.list(KNOWLEDGE_ROOT).orEmpty()
            .filter { it.endsWith(".md", ignoreCase = true) }
            .forEach { filename ->
                val content = context.assets.open("$KNOWLEDGE_ROOT/$filename").bufferedReader().use { it.readText() }
                database.replaceKnowledge(
                    seedKey = "asset:$filename",
                    sections = MarkdownSections.parse(content, filename.substringBeforeLast('.')),
                    curated = true,
                )
            }
    }

    companion object {
        private const val KNOWLEDGE_ROOT = "knowledge"
    }
}
