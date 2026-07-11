package com.offlineneuralfacilitator.onf.data

import com.offlineneuralfacilitator.onf.domain.model.OnfState
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

internal object SessionExporter {
    fun json(state: OnfState): ByteArray = SessionJsonCodec.encode(state).toByteArray(Charsets.UTF_8)

    fun markdown(state: OnfState): ByteArray = buildString {
        appendLine("# ${state.session.topic}")
        appendLine()
        appendLine("- Session: `${state.session.id}`")
        appendLine("- Started: ${format(state.session.startedAtEpochMs)}")
        appendLine("- Local processing only")
        appendLine()
        appendLine("## Decisions")
        if (state.decisions.isEmpty()) appendLine("- No explicit decisions recorded.")
        state.decisions.forEach { appendLine("- ${it.text}${it.rationale.takeIf(String::isNotBlank)?.let { reason -> " — $reason" }.orEmpty()}") }
        appendLine()
        appendLine("## Actions")
        if (state.actions.isEmpty()) appendLine("- No explicit actions recorded.")
        state.actions.forEach { appendLine("- [ ] ${it.text} — **${it.owner}** — ${it.due}") }
        appendLine()
        appendLine("## Risks and guidance")
        if (state.insights.isEmpty()) appendLine("- No facilitator insights recorded.")
        state.insights.forEach { insight ->
            append("- **${insight.title}:** ${insight.text}")
            insight.citation?.let { citation -> append(" _Source: ${citation}_") }
            appendLine()
        }
        appendLine()
        appendLine("## Transcript")
        state.transcript.forEach { message ->
            appendLine("**${message.speaker}** · ${format(message.timestampEpochMs)}")
            appendLine()
            appendLine(message.content)
            appendLine()
        }
    }.toByteArray(Charsets.UTF_8)

    private fun format(epochMs: Long): String = FORMATTER.format(Instant.ofEpochMilli(epochMs))

    private val FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss z")
        .withZone(ZoneId.systemDefault())
}
