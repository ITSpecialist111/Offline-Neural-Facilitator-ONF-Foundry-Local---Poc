package com.offlineneuralfacilitator.onf.rag

import kotlin.math.min

internal data class KnowledgeChunk(
    val id: Long = 0,
    val source: String,
    val section: String,
    val text: String,
    val curated: Boolean = false,
)

internal data class KnowledgeMatch(
    val chunk: KnowledgeChunk,
    val relevance: Float,
)

internal class RagRanker(
    private val embedding: LocalHashEmbedding = LocalHashEmbedding(),
) {
    fun search(query: String, chunks: List<KnowledgeChunk>, limit: Int = 3): List<KnowledgeMatch> {
        if (query.isBlank() || chunks.isEmpty()) return emptyList()
        val queryTerms = searchTerms(query)
        val querySet = queryTerms.toSet()
        val queryBigrams = queryTerms.zipWithNext().toSet()
        val queryVector = embedding.embed(query)

        return chunks.asSequence()
            .map { chunk ->
                val documentTerms = searchTerms(chunk.text)
                val documentSet = documentTerms.toSet()
                val lexical = querySet.count(documentSet::contains).toFloat() / querySet.size.coerceAtLeast(1)
                val phrase = queryBigrams.intersect(documentTerms.zipWithNext().toSet()).size.toFloat() /
                    queryBigrams.size.coerceAtLeast(1)
                val semantic = cosine(queryVector, embedding.embed(chunk.text)).coerceAtLeast(0f)
                val curatedBoost = if (chunk.curated && lexical >= 0.12f) 0.08f else 0f
                val relevance = min(1f, semantic * 0.52f + lexical * 0.34f + phrase * 0.14f + curatedBoost)
                KnowledgeMatch(chunk, relevance)
            }
            .sortedByDescending(KnowledgeMatch::relevance)
            .take(limit.coerceAtLeast(1))
            .toList()
    }

    private fun cosine(left: FloatArray, right: FloatArray): Float = left.indices.sumOf {
        (left[it] * right[it]).toDouble()
    }.toFloat()

    companion object {
        private val TOKEN = Regex("[a-z0-9][a-z0-9_-]+")
        private val STOPWORDS = setOf(
            "a", "an", "and", "are", "as", "at", "be", "before", "but", "by", "can", "do", "for",
            "from", "has", "have", "how", "i", "if", "in", "is", "it", "of", "on", "or", "our", "should",
            "that", "the", "their", "this", "to", "we", "what", "when", "where", "which", "who", "with",
        )

        internal fun searchTerms(text: String): List<String> = TOKEN.findAll(text.lowercase())
            .map(MatchResult::value)
            .filter { it.length > 1 && it !in STOPWORDS }
            .toList()
    }
}
