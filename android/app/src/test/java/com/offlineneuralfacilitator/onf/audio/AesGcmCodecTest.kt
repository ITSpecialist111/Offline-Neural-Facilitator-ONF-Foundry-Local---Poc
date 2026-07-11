package com.offlineneuralfacilitator.onf.audio

import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertThrows
import org.junit.Test
import javax.crypto.KeyGenerator

class AesGcmCodecTest {
    private val key = KeyGenerator.getInstance("AES").apply { init(256) }.generateKey()

    @Test
    fun `round trips an independently authenticated segment`() {
        val plain = ByteArray(32_000) { (it % 251).toByte() }
        val aad = "session-1:segment-7".toByteArray()
        val encrypted = AesGcmCodec.encrypt(key, plain, aad)
        val recovered = AesGcmCodec.decrypt(key, encrypted, aad)
        assertArrayEquals(plain, recovered)
    }

    @Test
    fun `rejects tampered ciphertext`() {
        val encrypted = AesGcmCodec.encrypt(key, "private audio".toByteArray())
        encrypted[encrypted.lastIndex] = (encrypted.last().toInt() xor 1).toByte()
        assertThrows(Exception::class.java) { AesGcmCodec.decrypt(key, encrypted) }
    }
}
