package com.offlineneuralfacilitator.onf.audio

import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.DataInputStream
import java.io.DataOutputStream
import javax.crypto.Cipher
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

internal object AesGcmCodec {
    private val magic = byteArrayOf('O'.code.toByte(), 'N'.code.toByte(), 'F'.code.toByte(), 'A'.code.toByte())
    private val defaultAad = "ONF-AUDIO-V1".toByteArray(Charsets.UTF_8)

    fun encrypt(key: SecretKey, plaintext: ByteArray, aad: ByteArray = defaultAad): ByteArray {
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.ENCRYPT_MODE, key)
        val iv = requireNotNull(cipher.iv).also {
            require(it.size in 12..32) { "The encryption provider returned an invalid GCM IV." }
        }
        cipher.updateAAD(aad)
        val ciphertext = cipher.doFinal(plaintext)
        return ByteArrayOutputStream(magic.size + 1 + 2 + 4 + iv.size + ciphertext.size).use { buffer ->
            DataOutputStream(buffer).use { output ->
                output.write(magic)
                output.writeByte(VERSION)
                output.writeShort(iv.size)
                output.writeInt(ciphertext.size)
                output.write(iv)
                output.write(ciphertext)
            }
            buffer.toByteArray()
        }
    }

    fun decrypt(key: SecretKey, payload: ByteArray, aad: ByteArray = defaultAad): ByteArray {
        val input = DataInputStream(ByteArrayInputStream(payload))
        val suppliedMagic = ByteArray(magic.size).also(input::readFully)
        require(suppliedMagic.contentEquals(magic)) { "Not an ONF encrypted audio segment." }
        require(input.readUnsignedByte() == VERSION) { "Unsupported ONF audio version." }
        val ivLength = input.readUnsignedShort()
        val cipherLength = input.readInt()
        require(ivLength in 12..32 && cipherLength in 16..MAX_SEGMENT_BYTES) { "Invalid encrypted audio header." }
        require(input.available() == ivLength + cipherLength) { "Encrypted audio segment is incomplete." }
        val iv = ByteArray(ivLength).also(input::readFully)
        val ciphertext = ByteArray(cipherLength).also(input::readFully)
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.DECRYPT_MODE, key, GCMParameterSpec(TAG_BITS, iv))
        cipher.updateAAD(aad)
        return cipher.doFinal(ciphertext)
    }

    private const val VERSION = 1
    private const val TAG_BITS = 128
    private const val MAX_SEGMENT_BYTES = 16 * 1024 * 1024
    private const val TRANSFORMATION = "AES/GCM/NoPadding"
}
