package com.offlineneuralfacilitator.onf.ai

import kotlinx.coroutines.flow.StateFlow

enum class EnginePhase {
    UNCONFIGURED,
    LOADING,
    READY,
    ERROR,
}

data class LlmStatus(
    val phase: EnginePhase = EnginePhase.UNCONFIGURED,
    val modelName: String? = null,
    val backend: String? = null,
    val message: String = "Import a Gemma 4 .litertlm model to enable generative reasoning.",
)

interface LocalLlmEngine : AutoCloseable {
    val status: StateFlow<LlmStatus>

    suspend fun load(modelPath: String, modelName: String)

    suspend fun generate(systemInstruction: String, prompt: String): String

    suspend fun transcribeAudio(wavBytes: ByteArray): String?
}
