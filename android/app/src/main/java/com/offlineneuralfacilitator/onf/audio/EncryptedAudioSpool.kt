package com.offlineneuralfacilitator.onf.audio

import android.content.Context
import java.io.File

data class AudioSegment(
    val sessionId: String,
    val index: Int,
    val file: File,
    val encryptedBytes: Long,
)

internal class EncryptedAudioSpool(
    context: Context,
) {
    private val root = File(context.filesDir, "audio_spool").apply(File::mkdirs)

    fun writeSegment(sessionId: String, index: Int, pcm: ByteArray, sampleRate: Int): AudioSegment {
        require(sessionId.matches(Regex("[A-Za-z0-9_-]{3,96}"))) { "Invalid session identifier." }
        require(index >= 0)
        val directory = File(root, sessionId).apply(File::mkdirs)
        val wav = WavCodec.pcm16Mono(pcm, sampleRate)
        val aad = aad(sessionId, index)
        val encrypted = AesGcmCodec.encrypt(AndroidKeyStoreKeyProvider.getOrCreate(), wav, aad)
        val destination = File(directory, "segment-${index.toString().padStart(6, '0')}.onfa")
        val temporary = File(directory, "${destination.name}.tmp")
        try {
            temporary.outputStream().buffered().use { output ->
                output.write(encrypted)
                output.flush()
            }
            check(!destination.exists() || destination.delete()) { "Could not replace an existing audio segment." }
            check(temporary.renameTo(destination)) { "Could not finalize encrypted audio segment." }
            return AudioSegment(sessionId, index, destination, destination.length())
        } finally {
            wav.fill(0)
            encrypted.fill(0)
            temporary.delete()
        }
    }

    fun readWav(segment: AudioSegment): ByteArray = AesGcmCodec.decrypt(
        AndroidKeyStoreKeyProvider.getOrCreate(),
        segment.file.readBytes(),
        aad(segment.sessionId, segment.index),
    )

    fun segments(sessionId: String): List<AudioSegment> {
        val directory = File(root, sessionId)
        return directory.listFiles { file -> file.extension == "onfa" }
            .orEmpty()
            .mapNotNull { file ->
                INDEX.find(file.name)?.groupValues?.getOrNull(1)?.toIntOrNull()?.let { index ->
                    AudioSegment(sessionId, index, file, file.length())
                }
            }
            .sortedBy(AudioSegment::index)
    }

    fun totalEncryptedBytes(sessionId: String): Long = segments(sessionId).sumOf(AudioSegment::encryptedBytes)

    private fun aad(sessionId: String, index: Int): ByteArray =
        "ONF-AUDIO-V1:$sessionId:$index".toByteArray(Charsets.UTF_8)

    companion object {
        private val INDEX = Regex("segment-(\\d{6})\\.onfa")
    }
}
