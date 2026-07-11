package com.offlineneuralfacilitator.onf.rag

import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.security.MessageDigest
import kotlin.math.ln
import kotlin.math.sqrt

class LocalHashEmbedding(
    private val dimensions: Int = DIMENSIONS,
) {
    fun embed(text: String): FloatArray {
        val counts = TOKEN.findAll(text.lowercase())
            .map(MatchResult::value)
            .groupingBy(String::toString)
            .eachCount()
        val vector = FloatArray(dimensions)
        val digest = MessageDigest.getInstance("SHA-256")

        counts.forEach { (token, frequency) ->
            val bytes = digest.digest(token.toByteArray(Charsets.UTF_8))
            val unsigned = ByteBuffer.wrap(bytes, 0, 4)
                .order(ByteOrder.LITTLE_ENDIAN)
                .int
                .toLong() and 0xffffffffL
            val index = (unsigned % dimensions).toInt()
            val sign = if ((bytes[4].toInt() and 0xff) % 2 == 0) 1f else -1f
            vector[index] += sign * (1f + ln(frequency.toFloat()))
        }

        val norm = sqrt(vector.sumOf { value -> (value * value).toDouble() }).toFloat().takeIf { it > 0f } ?: 1f
        return vector.apply { indices.forEach { this[it] /= norm } }
    }

    companion object {
        const val DIMENSIONS = 384
        const val NAME = "onf-local-hash-mobile-v1"
        private val TOKEN = Regex("[a-z0-9][a-z0-9_-]+")
    }
}
