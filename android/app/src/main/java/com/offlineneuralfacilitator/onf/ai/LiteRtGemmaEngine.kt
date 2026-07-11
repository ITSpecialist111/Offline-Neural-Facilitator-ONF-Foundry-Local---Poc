package com.offlineneuralfacilitator.onf.ai

import android.content.Context
import com.google.ai.edge.litertlm.Backend
import com.google.ai.edge.litertlm.Content
import com.google.ai.edge.litertlm.Contents
import com.google.ai.edge.litertlm.ConversationConfig
import com.google.ai.edge.litertlm.Engine
import com.google.ai.edge.litertlm.EngineConfig
import com.google.ai.edge.litertlm.LogSeverity
import com.google.ai.edge.litertlm.Message
import com.google.ai.edge.litertlm.SamplerConfig
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.TimeoutCancellationException
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import java.io.File

class LiteRtGemmaEngine(
    private val context: Context,
) : LocalLlmEngine {
    private val _status = MutableStateFlow(LlmStatus())
    override val status: StateFlow<LlmStatus> = _status.asStateFlow()

    @Volatile
    private var engine: Engine? = null

    override suspend fun load(modelPath: String, modelName: String) = withContext(Dispatchers.IO) {
        val model = File(modelPath)
        require(model.isFile && model.canRead()) { "The selected model is not readable." }
        _status.value = LlmStatus(EnginePhase.LOADING, modelName, message = "Loading Gemma into private device memory…")
        close()
        Engine.setNativeMinLogSeverity(LogSeverity.ERROR)

        val gpuAttempt = runCatching { createEngine(modelPath, Backend.GPU()) }
        val selected = gpuAttempt.getOrElse {
            runCatching { createEngine(modelPath, Backend.CPU()) }.getOrElse { cpuError ->
                _status.value = LlmStatus(
                    phase = EnginePhase.ERROR,
                    modelName = modelName,
                    message = "Model load failed on GPU and CPU: ${cpuError.message ?: it.message}",
                )
                throw cpuError
            }
        }
        engine = selected.first
        _status.value = LlmStatus(
            phase = EnginePhase.READY,
            modelName = modelName,
            backend = selected.second,
            message = "Gemma is ready. Inference remains on this device.",
        )
    }

    override suspend fun generate(systemInstruction: String, prompt: String): String = withContext(Dispatchers.Default) {
        val active = engine ?: error("No local model is loaded.")
        val config = ConversationConfig(
            systemInstruction = Contents.of(systemInstruction),
            samplerConfig = SamplerConfig(topK = 24, topP = 0.9, temperature = 0.25, seed = 11),
        )
        val conversation = active.createConversation(config)
        try {
            streamResponse(conversation, conversation.sendMessageAsync(prompt))
                .trim()
                .ifBlank { error("The local model returned an empty response.") }
        } finally {
            conversation.close()
        }
    }

    override suspend fun transcribeAudio(wavBytes: ByteArray): String? = withContext(Dispatchers.Default) {
        val active = engine ?: return@withContext null
        runCatching {
            val config = ConversationConfig(
                systemInstruction = Contents.of(
                    "Transcribe speech faithfully. Return only the spoken words. Do not summarize or add commentary.",
                ),
                samplerConfig = SamplerConfig(topK = 1, topP = 1.0, temperature = 0.0, seed = 7),
            )
            val conversation = active.createConversation(config)
            try {
                val content = Contents.of(
                    Content.AudioBytes(wavBytes),
                    Content.Text("Transcribe this meeting audio segment verbatim."),
                )
                streamResponse(conversation, conversation.sendMessageAsync(content)).trim()
            } finally {
                conversation.close()
            }.takeIf(String::isNotBlank)
        }.getOrNull()
    }

    @Synchronized
    override fun close() {
        engine?.close()
        engine = null
    }

    private fun createEngine(modelPath: String, backend: Backend): Pair<Engine, String> {
        val candidate = Engine(
            EngineConfig(
                modelPath = modelPath,
                backend = backend,
                visionBackend = backend,
                audioBackend = backend,
                maxNumTokens = 2_048,
                maxNumImages = 1,
                cacheDir = File(context.cacheDir, "litertlm").apply(File::mkdirs).absolutePath,
            ),
        )
        return try {
            candidate.initialize()
            candidate to backend.name
        } catch (error: Throwable) {
            runCatching(candidate::close)
            throw error
        }
    }

    private fun Message.plainText(): String = contents.contents
        .filterIsInstance<Content.Text>()
        .joinToString(separator = "") { it.text }

    private suspend fun streamResponse(
        conversation: com.google.ai.edge.litertlm.Conversation,
        messages: Flow<Message>,
    ): String = try {
        withTimeout(GENERATION_TIMEOUT_MS) {
            var output = ""
            messages.collect { message ->
                val next = message.plainText()
                output = if (next.startsWith(output)) next else output + next
            }
            output
        }
    } catch (error: TimeoutCancellationException) {
        runCatching(conversation::cancelProcess)
        throw IllegalStateException("Local Gemma generation exceeded the 45-second safety limit.", error)
    }

    companion object {
        private const val GENERATION_TIMEOUT_MS = 45_000L
    }
}
