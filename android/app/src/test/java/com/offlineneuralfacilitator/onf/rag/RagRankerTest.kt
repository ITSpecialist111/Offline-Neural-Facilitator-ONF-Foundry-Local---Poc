package com.offlineneuralfacilitator.onf.rag

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class RagRankerTest {
    @Test
    fun `ranks matching clean recovery evidence first`() {
        val chunks = listOf(
            KnowledgeChunk(source = "Continuity", section = "Recovery", text = "Verify immutable backup integrity in a clean room before restoring identity services.", curated = true),
            KnowledgeChunk(source = "Facilities", section = "Catering", text = "Lunch service begins at noon in the main hall.", curated = true),
        )
        val results = RagRanker().search("safest immutable backup recovery", chunks, 1)
        assertEquals("Recovery", results.single().chunk.section)
        assertTrue(results.single().relevance >= 0.24f)
    }

    @Test
    fun `embedding is deterministic and normalized`() {
        val embedding = LocalHashEmbedding()
        val left = embedding.embed("verified clean recovery")
        val right = embedding.embed("verified clean recovery")
        assertTrue(left.contentEquals(right))
        val norm = kotlin.math.sqrt(left.sumOf { (it * it).toDouble() })
        assertEquals(1.0, norm, 0.0001)
    }
}
