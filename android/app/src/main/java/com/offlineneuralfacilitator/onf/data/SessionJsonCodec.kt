package com.offlineneuralfacilitator.onf.data

import com.offlineneuralfacilitator.onf.domain.FacilitationRules
import com.offlineneuralfacilitator.onf.domain.model.ActionItem
import com.offlineneuralfacilitator.onf.domain.model.Decision
import com.offlineneuralfacilitator.onf.domain.model.Insight
import com.offlineneuralfacilitator.onf.domain.model.InsightKind
import com.offlineneuralfacilitator.onf.domain.model.OnfState
import com.offlineneuralfacilitator.onf.domain.model.SessionInfo
import com.offlineneuralfacilitator.onf.domain.model.SessionStatus
import com.offlineneuralfacilitator.onf.domain.model.Severity
import com.offlineneuralfacilitator.onf.domain.model.TopicSource
import com.offlineneuralfacilitator.onf.domain.model.TranscriptMessage
import org.json.JSONArray
import org.json.JSONObject

internal object SessionJsonCodec {
    fun encode(state: OnfState): String = JSONObject().apply {
        put("schema", 1)
        put("session", JSONObject().apply {
            put("id", state.session.id)
            put("status", state.session.status.name)
            put("topic", state.session.topic)
            put("topic_source", state.session.topicSource.name)
            put("started_at_epoch_ms", state.session.startedAtEpochMs)
        })
        put("transcript", state.transcript.toJsonArray { message -> JSONObject().apply {
            put("id", message.id)
            put("role", message.role)
            put("speaker", message.speaker)
            put("content", message.content)
            put("timestamp_epoch_ms", message.timestampEpochMs)
            put("source", message.source)
        } })
        put("insights", state.insights.toJsonArray { insight -> JSONObject().apply {
            put("id", insight.id)
            put("kind", insight.kind.name)
            put("title", insight.title)
            put("text", insight.text)
            put("severity", insight.severity.name)
            put("citation", insight.citation)
            put("source", insight.source)
            put("timestamp_epoch_ms", insight.timestampEpochMs)
        } })
        put("decisions", state.decisions.toJsonArray { decision -> JSONObject().apply {
            put("id", decision.id)
            put("text", decision.text)
            put("rationale", decision.rationale)
            put("timestamp_epoch_ms", decision.timestampEpochMs)
        } })
        put("actions", state.actions.toJsonArray { action -> JSONObject().apply {
            put("id", action.id)
            put("text", action.text)
            put("owner", action.owner)
            put("due", action.due)
            put("status", action.status)
            put("timestamp_epoch_ms", action.timestampEpochMs)
        } })
        put("active_skills", JSONArray(state.activeSkills.toList()))
    }.toString(2)

    fun decode(payload: String): OnfState {
        val root = JSONObject(payload)
        val sessionJson = root.getJSONObject("session")
        val session = SessionInfo(
            id = sessionJson.getString("id"),
            status = sessionJson.enum("status", SessionStatus.READY),
            topic = sessionJson.optString("topic", "Untitled session"),
            topicSource = sessionJson.enum("topic_source", TopicSource.PENDING),
            startedAtEpochMs = sessionJson.optLong("started_at_epoch_ms", System.currentTimeMillis()),
        )
        val transcript = root.optJSONArray("transcript").objects().map { item ->
            TranscriptMessage(
                id = item.getString("id"),
                role = item.optString("role", "participant"),
                speaker = item.optString("speaker", "Speaker"),
                content = item.getString("content"),
                timestampEpochMs = item.optLong("timestamp_epoch_ms", session.startedAtEpochMs),
                source = item.optString("source", "live"),
            )
        }
        val insights = root.optJSONArray("insights").objects().map { item ->
            Insight(
                id = item.getString("id"),
                kind = item.enum("kind", InsightKind.FACILITATION),
                title = item.getString("title"),
                text = item.getString("text"),
                severity = item.enum("severity", Severity.INFO),
                citation = item.optNullableString("citation"),
                source = item.optString("source", "facilitator"),
                timestampEpochMs = item.optLong("timestamp_epoch_ms", session.startedAtEpochMs),
            )
        }
        val decisions = root.optJSONArray("decisions").objects().map { item ->
            Decision(
                id = item.getString("id"),
                text = item.getString("text"),
                rationale = item.optString("rationale", ""),
                timestampEpochMs = item.optLong("timestamp_epoch_ms", session.startedAtEpochMs),
            )
        }
        val actions = root.optJSONArray("actions").objects().map { item ->
            ActionItem(
                id = item.getString("id"),
                text = item.getString("text"),
                owner = item.optString("owner", "Unassigned"),
                due = item.optString("due", "Not set"),
                status = item.optString("status", "open"),
                timestampEpochMs = item.optLong("timestamp_epoch_ms", session.startedAtEpochMs),
            )
        }
        val state = OnfState(
            session = session,
            transcript = transcript,
            insights = insights,
            decisions = decisions,
            actions = actions,
            risks = insights.filter { it.kind == InsightKind.RISK },
            activeSkills = root.optJSONArray("active_skills").strings().toSet(),
        )
        return state.copy(metrics = FacilitationRules.metrics(state))
    }

    private inline fun <T> Iterable<T>.toJsonArray(transform: (T) -> JSONObject): JSONArray =
        JSONArray().also { array -> forEach { array.put(transform(it)) } }

    private fun JSONArray?.objects(): List<JSONObject> = if (this == null) emptyList() else
        (0 until length()).map(::getJSONObject)

    private fun JSONArray?.strings(): List<String> = if (this == null) emptyList() else
        (0 until length()).map(::getString)

    private inline fun <reified T : Enum<T>> JSONObject.enum(key: String, fallback: T): T =
        runCatching { enumValueOf<T>(getString(key)) }.getOrDefault(fallback)

    private fun JSONObject.optNullableString(key: String): String? =
        if (isNull(key)) null else optString(key).takeIf(String::isNotBlank)
}
