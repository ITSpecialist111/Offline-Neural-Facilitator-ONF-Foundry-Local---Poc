package com.offlineneuralfacilitator.onf

import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.offlineneuralfacilitator.onf.audio.EncryptedAudioSpool
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class EncryptedAudioSpoolTest {
    @Test
    fun writesAndAuthenticatesSegmentWithAndroidKeyStore() {
        val context = ApplicationProvider.getApplicationContext<android.content.Context>()
        val spool = EncryptedAudioSpool(context)
        val sessionId = "instrumented-audio"
        val pcm = ByteArray(32_000) { (it % 173).toByte() }
        val segment = spool.writeSegment(sessionId, 0, pcm, 16_000)
        assertTrue(segment.file.isFile)
        assertTrue(segment.encryptedBytes > pcm.size)
        val wav = spool.readWav(segment)
        assertArrayEquals(pcm, wav.copyOfRange(44, wav.size))
    }
}
