package com.offlineneuralfacilitator.onf.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class MarkdownSectionsTest {
    @Test
    fun `keeps document and section citations`() {
        val sections = MarkdownSections.parse(
            """
                # Recovery Card
                ## Diversion threshold
                Divert after thirty minutes.
                ## Restore order
                Identity before EHR.
            """.trimIndent(),
            "fallback",
        )
        assertEquals(2, sections.size)
        assertEquals("Recovery Card", sections.first().source)
        assertEquals("Diversion threshold", sections.first().heading)
    }

    @Test
    fun `chunks long paragraphs with overlap`() {
        val text = (1..400).joinToString(" ") { "token$it" }
        val chunks = MarkdownSections.chunks(text, size = 200, overlap = 30)
        assertTrue(chunks.size > 1)
        assertTrue(chunks.all(String::isNotBlank))
    }
}
