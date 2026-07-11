package com.offlineneuralfacilitator.onf.data

internal data class MarkdownSection(
    val source: String,
    val heading: String,
    val body: String,
)

internal object MarkdownSections {
    private val lineBreak = Regex("\\r\\n?")
    private val heading = Regex("^#{2,3}\\s+")

    fun parse(content: String, fallbackTitle: String): List<MarkdownSection> {
        var source = fallbackTitle
        var currentHeading = "Overview"
        val buffer = mutableListOf<String>()
        val sections = mutableListOf<MarkdownSection>()

        fun flush() {
            val body = buffer.joinToString("\n").trim()
            if (body.isNotBlank()) sections += MarkdownSection(source, currentHeading, body)
            buffer.clear()
        }

        content.replace(lineBreak, "\n").lineSequence().forEach { line ->
            when {
                line.startsWith("# ") -> source = line.removePrefix("# ").trim().ifBlank { fallbackTitle }
                heading.containsMatchIn(line) -> {
                    flush()
                    currentHeading = line.replace(heading, "").trim().ifBlank { "Overview" }
                }
                else -> buffer += line
            }
        }
        flush()
        return sections
    }

    fun chunks(text: String, size: Int = 900, overlap: Int = 120): List<String> {
        val clean = text.replace(lineBreak, "\n").trim()
        if (clean.isBlank()) return emptyList()
        return clean.split(Regex("\\n{2,}"))
            .asSequence()
            .map(String::trim)
            .filter(String::isNotBlank)
            .flatMap { paragraph ->
                sequence {
                    var cursor = 0
                    while (cursor < paragraph.length) {
                        var end = (cursor + size).coerceAtMost(paragraph.length)
                        if (end < paragraph.length) {
                            val boundary = paragraph.lastIndexOf(' ', end - 1, ignoreCase = false)
                            if (boundary > cursor + size / 2) end = boundary
                        }
                        paragraph.substring(cursor, end).trim().takeIf(String::isNotBlank)?.let { yield(it) }
                        if (end >= paragraph.length) break
                        cursor = (end - overlap).coerceAtLeast(cursor + 1)
                    }
                }
            }
            .toList()
    }
}
