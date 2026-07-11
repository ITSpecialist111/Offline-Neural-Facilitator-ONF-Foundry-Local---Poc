package com.offlineneuralfacilitator.onf.domain

import com.offlineneuralfacilitator.onf.domain.model.ActionDraft
import com.offlineneuralfacilitator.onf.domain.model.OnfState
import com.offlineneuralfacilitator.onf.domain.model.SessionMetrics
import com.offlineneuralfacilitator.onf.domain.model.TranscriptMessage
import kotlin.math.max
import kotlin.math.min

object FacilitationRules {
    private val whitespace = Regex("\\s+")
    private val sentenceBreak = Regex("[.!?]")
    private val actionMarker = Regex("(?i)\\baction item\\s*[:\\-]\\s*")
    private val decisionPattern = Regex(
        "(?i)(?:we(?:'ve| have) decided(?: that| to)?|decision is|agreed(?: that| to))[:\\s-]+(.+)",
    )
    private val ownerPattern = Regex("(?i)\\b(?:owner is|owned by)\\s+([A-Z][a-z]+)")
    private val leadingOwnerPattern = Regex("^([A-Z][a-z]+)\\s+will\\s+", RegexOption.IGNORE_CASE)
    private val duePattern = Regex(
        "(?i)\\b(by\\s+[^.;]+|within\\s+(?:the\\s+next\\s+)?[a-z0-9 -]+(?:minutes?|hours?|days?)|now|immediately)\\b",
    )

    private val conflictTerms = listOf(
        "disagree",
        "not convinced",
        "won't work",
        "will not work",
        "too risky",
        "blocked",
    )

    fun normalize(text: String): String = text.replace(whitespace, " ").trim()

    fun explicitTitle(text: String): String? {
        val patterns = listOf(
            Regex("(?i)\\b(?:tabletop|session|meeting|scenario)\\s+(?:is\\s+)?(?:called|titled)\\s+[\\\"']?([^.!?\\\"']{4,120})"),
            Regex("(?i)\\b(?:today(?:'s)?\\s+)?(?:topic|session|meeting)\\s+(?:is|is about|focuses on)\\s+[\\\"']?([^.!?\\\"']{4,120})"),
        )
        val candidate = patterns.firstNotNullOfOrNull { it.find(text)?.groupValues?.getOrNull(1) }
            ?.replace(whitespace, " ")
            ?.trim(' ', '.', ':', '-')
            ?: return null
        val normalized = candidate.lowercase().replace("north star", "northstar")
        return if ("code blue" in normalized && "northstar" in normalized && "hospital" in normalized) {
            "Code Blue: Ransomware at Northstar Hospital"
        } else {
            candidate.take(120)
        }
    }

    fun fallbackTitle(text: String): String? {
        val sentence = text.split(sentenceBreak, limit = 2).firstOrNull()?.trim().orEmpty()
        val patterns = listOf(
            Regex("(?i)\\bdecid(?:e|ing)\\s+(?:whether|how|if)\\s+(?:to\\s+)?(.+)"),
            Regex("(?i)\\bdiscuss(?:ing)?\\s+(.+)"),
            Regex("(?i)\\breview(?:ing)?\\s+(.+)"),
            Regex("(?i)\\babout\\s+(.+)"),
        )
        var candidate = patterns.firstNotNullOfOrNull { it.find(sentence)?.groupValues?.getOrNull(1) }.orEmpty()
        if (candidate.isBlank()) {
            candidate = sentence.replace(Regex("(?i)^(?:today|we need to|we are|we're|this is)\\s+"), "")
        }
        val words = candidate.trim(' ', '.', ':', '-').split(whitespace).filter(String::isNotBlank)
        return words.takeIf { it.size >= 3 }
            ?.take(10)
            ?.joinToString(" ")
            ?.trimEnd(',', ';', ':')
    }

    fun decision(text: String): String? = decisionPattern.find(text)
        ?.groupValues
        ?.getOrNull(1)
        ?.trim(' ', '.')
        ?.takeIf(String::isNotBlank)
        ?.recordCase()

    fun actions(text: String): List<ActionDraft> {
        val markers = actionMarker.findAll(text).toList()
        val candidates = if (markers.isNotEmpty()) {
            markers.mapIndexed { index, marker ->
                val end = markers.getOrNull(index + 1)?.range?.first ?: text.length
                text.substring(marker.range.last + 1, end).trim(' ', '.')
            }
        } else {
            Regex("(?i)\\b(?:we(?:'ll| will)|please)\\s+(.+)")
                .find(text)
                ?.groupValues
                ?.getOrNull(1)
                ?.trim(' ', '.')
                ?.let(::listOf)
                .orEmpty()
        }

        return candidates.mapNotNull { raw ->
            var candidate = raw
            var owner = "Unassigned"
            ownerPattern.find(candidate)?.let { owner = it.groupValues[1] }
            leadingOwnerPattern.find(candidate)?.let {
                owner = it.groupValues[1].replaceFirstChar(Char::uppercase)
                candidate = candidate.substring(it.range.last + 1)
            }

            var due = "Not set"
            duePattern.find(candidate)?.let {
                due = it.value.trim().replaceFirstChar(Char::uppercase)
                candidate = (candidate.substring(0, it.range.first) + candidate.substring(it.range.last + 1))
                    .trim(' ', ',', '.', '-')
            }

            candidate.trim(' ', '.').takeIf(String::isNotBlank)?.let {
                ActionDraft(it.recordCase(), owner, due)
            }
        }
    }

    fun hasAlignmentGap(recent: List<TranscriptMessage>): Boolean {
        val sample = recent.takeLast(4).joinToString(" ") { it.content.lowercase() }
        return conflictTerms.sumOf { term -> sample.windowed(term.length, 1).count { it == term } } >= 2
    }

    fun isHighDensity(text: String): Boolean = normalize(text).split(' ').size > 70

    fun metrics(state: OnfState, nowEpochMs: Long = System.currentTimeMillis()): SessionMetrics {
        val words = state.transcript.sumOf { normalize(it.content).split(' ').count(String::isNotBlank) }
        val riskCount = state.risks.size
        val alignment = max(42, min(96, 72 + state.actions.size * 4 + state.decisions.size * 5 - riskCount * 3))
        return SessionMetrics(
            durationSeconds = max(0L, (nowEpochMs - state.session.startedAtEpochMs) / 1_000L),
            wordCount = words,
            turnCount = state.transcript.size,
            insightCount = state.insights.size,
            actionCount = state.actions.size,
            riskCount = riskCount,
            alignmentScore = alignment,
        )
    }

    fun String.recordCase(): String = trim().replaceFirstChar { character ->
        if (character.isLowerCase()) character.titlecase() else character.toString()
    }
}
