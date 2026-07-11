package com.offlineneuralfacilitator.onf.audio

import android.content.Context
import android.content.Intent
import androidx.core.content.ContextCompat

object AudioCaptureController {
    fun start(context: Context, sessionId: String) {
        ContextCompat.startForegroundService(
            context,
            Intent(context, AudioCaptureService::class.java)
                .setAction(AudioCaptureService.ACTION_START)
                .putExtra(AudioCaptureService.EXTRA_SESSION_ID, sessionId),
        )
    }

    fun stop(context: Context) {
        context.startService(
            Intent(context, AudioCaptureService::class.java).setAction(AudioCaptureService.ACTION_STOP),
        )
    }
}
