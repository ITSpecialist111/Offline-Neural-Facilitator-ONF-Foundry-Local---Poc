package com.offlineneuralfacilitator.onf.audio

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

data class RecordingState(
    val isRecording: Boolean = false,
    val sessionId: String? = null,
    val segmentCount: Int = 0,
    val encryptedBytes: Long = 0,
    val elapsedMs: Long = 0,
    val error: String? = null,
)

object RecordingStateStore {
    private val mutable = MutableStateFlow(RecordingState())
    val state: StateFlow<RecordingState> = mutable.asStateFlow()

    internal fun update(value: RecordingState) {
        mutable.value = value
    }
}
