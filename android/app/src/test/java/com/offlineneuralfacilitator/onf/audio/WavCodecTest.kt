package com.offlineneuralfacilitator.onf.audio

import org.junit.Assert.assertEquals
import org.junit.Test

class WavCodecTest {
    @Test
    fun `writes a valid mono PCM header`() {
        val wav = WavCodec.pcm16Mono(ByteArray(32_000), 16_000)
        assertEquals("RIFF", wav.copyOfRange(0, 4).toString(Charsets.US_ASCII))
        assertEquals("WAVE", wav.copyOfRange(8, 12).toString(Charsets.US_ASCII))
        assertEquals("data", wav.copyOfRange(36, 40).toString(Charsets.US_ASCII))
        assertEquals(32_044, wav.size)
    }
}
