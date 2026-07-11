package com.offlineneuralfacilitator.onf.audio

import java.io.ByteArrayOutputStream
import java.io.DataOutputStream

internal object WavCodec {
    fun pcm16Mono(pcm: ByteArray, sampleRate: Int): ByteArray {
        require(sampleRate in 8_000..96_000)
        require(pcm.size % 2 == 0) { "PCM16 data must contain complete samples." }
        val byteRate = sampleRate * CHANNELS * BITS_PER_SAMPLE / 8
        val blockAlign = CHANNELS * BITS_PER_SAMPLE / 8
        return ByteArrayOutputStream(HEADER_BYTES + pcm.size).use { buffer ->
            DataOutputStream(buffer).use { output ->
                output.writeAscii("RIFF")
                output.writeLittleEndianInt(36 + pcm.size)
                output.writeAscii("WAVE")
                output.writeAscii("fmt ")
                output.writeLittleEndianInt(16)
                output.writeLittleEndianShort(1)
                output.writeLittleEndianShort(CHANNELS)
                output.writeLittleEndianInt(sampleRate)
                output.writeLittleEndianInt(byteRate)
                output.writeLittleEndianShort(blockAlign)
                output.writeLittleEndianShort(BITS_PER_SAMPLE)
                output.writeAscii("data")
                output.writeLittleEndianInt(pcm.size)
                output.write(pcm)
            }
            buffer.toByteArray()
        }
    }

    private fun DataOutputStream.writeAscii(value: String) = write(value.toByteArray(Charsets.US_ASCII))

    private fun DataOutputStream.writeLittleEndianInt(value: Int) {
        writeByte(value and 0xff)
        writeByte(value shr 8 and 0xff)
        writeByte(value shr 16 and 0xff)
        writeByte(value shr 24 and 0xff)
    }

    private fun DataOutputStream.writeLittleEndianShort(value: Int) {
        writeByte(value and 0xff)
        writeByte(value shr 8 and 0xff)
    }

    private const val HEADER_BYTES = 44
    private const val CHANNELS = 1
    private const val BITS_PER_SAMPLE = 16
}
