package com.offlineneuralfacilitator.onf.audio

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.content.pm.PackageManager
import android.content.pm.ServiceInfo
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.os.Build
import android.os.IBinder
import android.os.SystemClock
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import com.offlineneuralfacilitator.onf.MainActivity
import com.offlineneuralfacilitator.onf.R
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.io.ByteArrayOutputStream
import java.util.concurrent.atomic.AtomicBoolean

class AudioCaptureService : Service() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val stopping = AtomicBoolean(false)
    private var captureJob: Job? = null
    @Volatile
    private var recorder: AudioRecord? = null

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START -> startCapture(intent.getStringExtra(EXTRA_SESSION_ID))
            ACTION_STOP -> stopCapture()
        }
        return START_NOT_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        stopCapture()
        scope.cancel()
        super.onDestroy()
    }

    private fun startCapture(sessionId: String?) {
        if (captureJob?.isActive == true) return
        if (sessionId.isNullOrBlank()) return fail("A valid session is required for recording.")
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            return fail("Microphone permission is not granted.")
        }
        stopping.set(false)
        val notification = notification(0L, 0)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            startForeground(NOTIFICATION_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE)
        } else if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(NOTIFICATION_ID, notification, 0)
        } else {
            startForeground(NOTIFICATION_ID, notification)
        }
        captureJob = scope.launch { capture(sessionId) }
    }

    @Suppress("MissingPermission")
    private suspend fun capture(sessionId: String) {
        val minimum = AudioRecord.getMinBufferSize(SAMPLE_RATE, CHANNEL_CONFIG, AUDIO_FORMAT)
        if (minimum <= 0) return fail("This device cannot initialize a 16 kHz microphone stream.")
        val bufferSize = maxOf(minimum * 2, 8_192)
        val localRecorder = AudioRecord.Builder()
            .setAudioSource(MediaRecorder.AudioSource.VOICE_RECOGNITION)
            .setAudioFormat(
                AudioFormat.Builder()
                    .setEncoding(AUDIO_FORMAT)
                    .setSampleRate(SAMPLE_RATE)
                    .setChannelMask(CHANNEL_CONFIG)
                    .build(),
            )
            .setBufferSizeInBytes(bufferSize)
            .build()
        if (localRecorder.state != AudioRecord.STATE_INITIALIZED) {
            localRecorder.release()
            return fail("The microphone could not be initialized.")
        }
        recorder = localRecorder
        val spool = EncryptedAudioSpool(this)
        var segmentIndex = spool.segments(sessionId).lastOrNull()?.index?.plus(1) ?: 0
        var encryptedBytes = spool.totalEncryptedBytes(sessionId)
        val started = SystemClock.elapsedRealtime()
        val segmentBuffer = ByteArrayOutputStream(SEGMENT_BYTES)
        val readBuffer = ByteArray(bufferSize)
        var terminalError: String? = null

        try {
            localRecorder.startRecording()
            RecordingStateStore.update(RecordingState(true, sessionId, segmentIndex, encryptedBytes, 0))
            while (scope.isActive && !stopping.get()) {
                val count = localRecorder.read(readBuffer, 0, readBuffer.size, AudioRecord.READ_BLOCKING)
                if (count <= 0) {
                    if (count == AudioRecord.ERROR_DEAD_OBJECT) throw IllegalStateException("Microphone stream ended unexpectedly.")
                    continue
                }
                segmentBuffer.write(readBuffer, 0, count)
                if (segmentBuffer.size() >= SEGMENT_BYTES) {
                    val pcm = segmentBuffer.toByteArray()
                    segmentBuffer.reset()
                    try {
                        val saved = spool.writeSegment(sessionId, segmentIndex, pcm, SAMPLE_RATE)
                        segmentIndex += 1
                        encryptedBytes += saved.encryptedBytes
                    } finally {
                        pcm.fill(0)
                    }
                }
                val elapsed = SystemClock.elapsedRealtime() - started
                RecordingStateStore.update(RecordingState(true, sessionId, segmentIndex, encryptedBytes, elapsed))
                updateNotification(elapsed, segmentIndex)
            }
        } catch (error: Throwable) {
            terminalError = error.message ?: error::class.java.simpleName
            if (!stopping.get()) {
                RecordingStateStore.update(
                    RecordingState(false, sessionId, segmentIndex, encryptedBytes, SystemClock.elapsedRealtime() - started, terminalError),
                )
            }
        } finally {
            if (segmentBuffer.size() > MIN_FINAL_SEGMENT_BYTES) {
                try {
                    val pcm = segmentBuffer.toByteArray()
                    try {
                        val saved = spool.writeSegment(sessionId, segmentIndex, pcm, SAMPLE_RATE)
                        segmentIndex += 1
                        encryptedBytes += saved.encryptedBytes
                    } finally {
                        pcm.fill(0)
                    }
                } catch (error: Throwable) {
                    terminalError = error.message ?: error::class.java.simpleName
                }
            }
            readBuffer.fill(0)
            segmentBuffer.reset()
            runCatching { localRecorder.stop() }
            localRecorder.release()
            recorder = null
            RecordingStateStore.update(
                RecordingState(
                    false,
                    sessionId,
                    segmentIndex,
                    encryptedBytes,
                    SystemClock.elapsedRealtime() - started,
                    terminalError,
                ),
            )
            stopForeground(STOP_FOREGROUND_REMOVE)
            stopSelf()
        }
    }

    private fun stopCapture() {
        if (!stopping.compareAndSet(false, true)) return
        runCatching { recorder?.stop() }
        if (captureJob?.isActive != true) {
            stopForeground(STOP_FOREGROUND_REMOVE)
            stopSelf()
        }
    }

    private fun fail(message: String) {
        RecordingStateStore.update(RecordingState(error = message))
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    private fun notification(elapsedMs: Long, segments: Int) = NotificationCompat.Builder(this, CHANNEL_ID)
        .setSmallIcon(R.drawable.ic_onf_app)
        .setContentTitle(getString(R.string.notification_recording_title))
        .setContentText("${formatElapsed(elapsedMs)} · $segments encrypted segments")
        .setOngoing(true)
        .setSilent(true)
        .setCategory(NotificationCompat.CATEGORY_SERVICE)
        .setContentIntent(
            PendingIntent.getActivity(
                this,
                0,
                Intent(this, MainActivity::class.java),
                PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
            ),
        )
        .addAction(
            0,
            "Stop",
            PendingIntent.getService(
                this,
                1,
                Intent(this, AudioCaptureService::class.java).setAction(ACTION_STOP),
                PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
            ),
        )
        .build()

    private fun updateNotification(elapsedMs: Long, segments: Int) {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED ||
            Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU
        ) {
            NotificationManagerCompat.from(this).notify(NOTIFICATION_ID, notification(elapsedMs, segments))
        }
    }

    private fun createNotificationChannel() {
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(
            NotificationChannel(
                CHANNEL_ID,
                getString(R.string.notification_channel_recording),
                NotificationManager.IMPORTANCE_LOW,
            ).apply {
                description = "Visible while ONF captures and encrypts meeting audio on this device."
                setShowBadge(false)
            },
        )
    }

    private fun formatElapsed(elapsedMs: Long): String {
        val totalSeconds = elapsedMs / 1_000
        return "%02d:%02d".format(totalSeconds / 60, totalSeconds % 60)
    }

    companion object {
        const val ACTION_START = "com.offlineneuralfacilitator.onf.action.START_CAPTURE"
        const val ACTION_STOP = "com.offlineneuralfacilitator.onf.action.STOP_CAPTURE"
        const val EXTRA_SESSION_ID = "session_id"
        private const val CHANNEL_ID = "onf_private_capture"
        private const val NOTIFICATION_ID = 1701
        private const val SAMPLE_RATE = 16_000
        private const val CHANNEL_CONFIG = AudioFormat.CHANNEL_IN_MONO
        private const val AUDIO_FORMAT = AudioFormat.ENCODING_PCM_16BIT
        private const val SEGMENT_SECONDS = 5
        private const val SEGMENT_BYTES = SAMPLE_RATE * 2 * SEGMENT_SECONDS
        private const val MIN_FINAL_SEGMENT_BYTES = SAMPLE_RATE
    }
}
