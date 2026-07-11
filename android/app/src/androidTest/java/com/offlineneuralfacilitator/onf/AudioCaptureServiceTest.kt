package com.offlineneuralfacilitator.onf

import android.Manifest
import androidx.test.core.app.ActivityScenario
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.rule.GrantPermissionRule
import com.offlineneuralfacilitator.onf.audio.AudioCaptureController
import com.offlineneuralfacilitator.onf.audio.EncryptedAudioSpool
import com.offlineneuralfacilitator.onf.audio.RecordingStateStore
import kotlinx.coroutines.flow.filter
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import java.util.UUID

@RunWith(AndroidJUnit4::class)
class AudioCaptureServiceTest {
    @get:Rule
    val permissions: GrantPermissionRule = GrantPermissionRule.grant(
        Manifest.permission.RECORD_AUDIO,
        Manifest.permission.POST_NOTIFICATIONS,
    )

    @Test
    fun foregroundCapturePersistsEncryptedSegment() = runBlocking {
        val context = ApplicationProvider.getApplicationContext<android.content.Context>()
        val sessionId = "service-${UUID.randomUUID().toString().take(8)}"
        ActivityScenario.launch(MainActivity::class.java).use {
            try {
                AudioCaptureController.start(context, sessionId)
                val recording = withTimeout(20_000) {
                    RecordingStateStore.state
                        .filter { state -> state.sessionId == sessionId && state.segmentCount >= 1 }
                        .first()
                }
                assertTrue(recording.isRecording)
                assertTrue(recording.encryptedBytes > 0)
            } finally {
                AudioCaptureController.stop(context)
            }
            withTimeout(10_000) {
                RecordingStateStore.state.filter { state -> !state.isRecording }.first()
            }
        }
        val segments = EncryptedAudioSpool(context).segments(sessionId)
        assertTrue(segments.isNotEmpty())
        assertTrue(segments.first().encryptedBytes > 32_000)
    }
}
