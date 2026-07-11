package com.offlineneuralfacilitator.onf.ui

import android.app.Application
import android.net.Uri
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.offlineneuralfacilitator.onf.OnfApplication
import com.offlineneuralfacilitator.onf.ai.EnginePhase
import com.offlineneuralfacilitator.onf.ai.FoundryCompanionDetector
import com.offlineneuralfacilitator.onf.ai.FoundryCompanionStatus
import com.offlineneuralfacilitator.onf.ai.GalleryDetector
import com.offlineneuralfacilitator.onf.ai.GalleryStatus
import com.offlineneuralfacilitator.onf.ai.LlmStatus
import com.offlineneuralfacilitator.onf.ai.ModelDescriptor
import com.offlineneuralfacilitator.onf.audio.AudioCaptureController
import com.offlineneuralfacilitator.onf.audio.EncryptedAudioSpool
import com.offlineneuralfacilitator.onf.audio.RecordingState
import com.offlineneuralfacilitator.onf.audio.RecordingStateStore
import com.offlineneuralfacilitator.onf.data.SessionExporter
import com.offlineneuralfacilitator.onf.domain.model.OnfState
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

data class MainUiState(
    val session: OnfState = OnfState(),
    val recording: RecordingState = RecordingState(),
    val llm: LlmStatus = LlmStatus(),
    val initialized: Boolean = false,
    val busyLabel: String? = null,
    val notice: String? = null,
    val knowledgeCount: Int = 0,
    val modelImportProgress: Float? = null,
    val foundryCompanion: FoundryCompanionStatus = FoundryCompanionStatus(),
    val gallery: GalleryStatus = GalleryStatus(),
    val deviceModels: List<ModelDescriptor> = emptyList(),
    val selectedModelPath: String? = null,
)

data class ExportPayload(
    val filename: String,
    val mimeType: String,
    val bytes: ByteArray,
)

private data class EphemeralUiState(
    val initialized: Boolean = false,
    val busyLabel: String? = null,
    val notice: String? = null,
    val knowledgeCount: Int = 0,
    val modelImportProgress: Float? = null,
    val foundryCompanion: FoundryCompanionStatus = FoundryCompanionStatus(),
    val gallery: GalleryStatus = GalleryStatus(),
    val deviceModels: List<ModelDescriptor> = emptyList(),
    val selectedModelPath: String? = null,
)

class MainViewModel(application: Application) : AndroidViewModel(application) {
    private val container = (application as OnfApplication).container
    private val facilitator = container.facilitator
    private val ephemeral = MutableStateFlow(EphemeralUiState())

    val uiState = combine(
        facilitator.state,
        RecordingStateStore.state,
        container.llm.status,
        ephemeral,
    ) { session, recording, llm, local ->
        MainUiState(
            session = session,
            recording = recording,
            llm = llm,
            initialized = local.initialized,
            busyLabel = local.busyLabel,
            notice = local.notice,
            knowledgeCount = local.knowledgeCount,
            modelImportProgress = local.modelImportProgress,
            foundryCompanion = local.foundryCompanion,
            gallery = local.gallery,
            deviceModels = local.deviceModels,
            selectedModelPath = local.selectedModelPath,
        )
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), MainUiState())

    init {
        viewModelScope.launch {
            runCatching {
                facilitator.initialize()
                val selectedModel = container.modelManager.selected()
                ephemeral.value = ephemeral.value.copy(
                    initialized = true,
                    knowledgeCount = facilitator.knowledgeCount(),
                    foundryCompanion = FoundryCompanionDetector.inspect(getApplication()),
                    gallery = GalleryDetector.inspect(getApplication()),
                    deviceModels = container.modelManager.available(),
                    selectedModelPath = selectedModel?.path,
                )
                selectedModel?.let { descriptor ->
                    loadModel(descriptor.path, descriptor.name)
                }
            }.onFailure { error ->
                ephemeral.value = ephemeral.value.copy(
                    initialized = true,
                    notice = "Private workspace initialization failed: ${error.message}",
                )
            }
        }
    }

    fun newSession(topic: String) = launchTask("Opening private workspace") {
        if (uiState.value.recording.isRecording) AudioCaptureController.stop(getApplication())
        facilitator.newSession(topic)
        RecordingStateStore.update(RecordingState())
        postNotice("Private workspace opened")
    }

    fun addTurn(text: String, speaker: String) = launchTask("Analyzing local turn") {
        facilitator.addParticipantText(text, speaker.ifBlank { "Speaker" })
    }

    fun ask(query: String) = launchTask("Reasoning on device") {
        facilitator.ask(query)
    }

    fun runShowcase() = launchTask("Running private showcase") {
        if (uiState.value.recording.isRecording) AudioCaptureController.stop(getApplication())
        facilitator.runShowcase()
        postNotice("Code Blue showcase is ready")
    }

    fun startRecording() {
        AudioCaptureController.start(getApplication(), uiState.value.session.session.id)
    }

    fun stopRecording() {
        AudioCaptureController.stop(getApplication())
    }

    fun transcribeLatestAudio() = launchTask("Transcribing locally") {
        check(container.llm.status.value.phase == EnginePhase.READY) { "Load a multimodal Gemma model first." }
        val sessionId = uiState.value.session.session.id
        val spool = EncryptedAudioSpool(getApplication())
        val latest = spool.segments(sessionId).lastOrNull() ?: error("No encrypted audio segment is available.")
        val wav = withContext(Dispatchers.IO) { spool.readWav(latest) }
        try {
            val transcript = container.llm.transcribeAudio(wav)
                ?: error("This Gemma model does not expose audio transcription.")
            facilitator.addParticipantText(transcript, speaker = "Local audio", source = "gemma-audio")
            postNotice("Latest encrypted segment transcribed on device")
        } finally {
            wav.fill(0)
        }
    }

    fun importModel(uri: Uri) = launchTask("Importing Gemma model") {
        val previous = container.modelManager.selected()
        ephemeral.value = ephemeral.value.copy(modelImportProgress = 0f)
        val descriptor = container.modelManager.import(uri) { progress ->
            ephemeral.value = ephemeral.value.copy(modelImportProgress = progress)
        }
        try {
            loadModel(descriptor.path, descriptor.name)
            container.modelManager.select(descriptor)
            refreshModels()
        } catch (error: Throwable) {
            container.modelManager.discard(descriptor)
            refreshModels()
            restoreModel(previous)
            throw error
        }
        ephemeral.value = ephemeral.value.copy(modelImportProgress = null)
        postNotice("${descriptor.name} is ready for private reasoning")
    }

    fun selectModel(path: String) = launchTask("Switching private model") {
        val previous = container.modelManager.selected()
        val descriptor = container.modelManager.available().firstOrNull { it.path == path }
            ?: error("The selected model is no longer available.")
        if (descriptor.path == ephemeral.value.selectedModelPath && container.llm.status.value.phase == EnginePhase.READY) {
            postNotice("${descriptor.name} is already active")
            return@launchTask
        }
        try {
            loadModel(descriptor.path, descriptor.name)
            container.modelManager.select(descriptor)
            refreshModels()
            postNotice("Switched to ${descriptor.name}")
        } catch (error: Throwable) {
            restoreModel(previous)
            throw error
        }
    }

    fun removeModel(path: String) = launchTask("Removing private model") {
        val descriptor = container.modelManager.available().firstOrNull { it.path == path }
            ?: error("The selected model is no longer available.")
        check(descriptor.path != ephemeral.value.selectedModelPath) { "Switch models before removing the active model." }
        check(container.modelManager.remove(descriptor)) { "The model could not be removed." }
        refreshModels()
        postNotice("Removed ${descriptor.name}")
    }

    fun importKnowledge(uri: Uri) = launchTask("Indexing local knowledge") {
        val resolver = getApplication<Application>().contentResolver
        val filename = resolver.query(uri, arrayOf(android.provider.OpenableColumns.DISPLAY_NAME), null, null, null)
            ?.use { cursor -> if (cursor.moveToFirst()) cursor.getString(0) else null }
            ?: "local-knowledge.md"
        val content = withContext(Dispatchers.IO) {
            resolver.openInputStream(uri)?.bufferedReader()?.use { reader ->
                val text = reader.readText()
                require(text.length <= MAX_KNOWLEDGE_CHARS) { "Knowledge file is larger than the 5 MB import limit." }
                text
            }
        } ?: error("The selected knowledge file could not be opened.")
        val chunks = facilitator.importKnowledge(filename, content)
        ephemeral.value = ephemeral.value.copy(knowledgeCount = facilitator.knowledgeCount())
        postNotice("Indexed $chunks local knowledge chunks")
    }

    fun export(kind: String): ExportPayload {
        val state = uiState.value.session
        val stamp = DateTimeFormatter.ofPattern("yyyyMMdd-HHmm").format(LocalDateTime.now())
        return if (kind == "json") {
            ExportPayload("ONF-$stamp.json", "application/json", SessionExporter.json(state))
        } else {
            ExportPayload("ONF-$stamp.md", "text/markdown", SessionExporter.markdown(state))
        }
    }

    fun clearNotice() {
        ephemeral.value = ephemeral.value.copy(notice = null)
    }

    fun reportNotice(message: String) {
        postNotice(message)
    }

    private suspend fun loadModel(path: String, name: String) {
        ephemeral.value = ephemeral.value.copy(busyLabel = "Loading Gemma into device memory")
        container.llm.load(path, name)
        ephemeral.value = ephemeral.value.copy(busyLabel = null, modelImportProgress = null)
    }

    private fun refreshModels() {
        val selected = container.modelManager.selected()
        ephemeral.value = ephemeral.value.copy(
            deviceModels = container.modelManager.available(),
            selectedModelPath = selected?.path,
        )
    }

    private suspend fun restoreModel(previous: ModelDescriptor?) {
        previous ?: return
        runCatching { loadModel(previous.path, previous.name) }
        refreshModels()
    }

    private fun launchTask(label: String, block: suspend () -> Unit) {
        if (ephemeral.value.busyLabel != null) return
        viewModelScope.launch {
            ephemeral.value = ephemeral.value.copy(busyLabel = label, notice = null)
            runCatching { block() }
                .onFailure { error -> postNotice(error.message ?: "$label failed") }
            ephemeral.value = ephemeral.value.copy(busyLabel = null, modelImportProgress = null)
        }
    }

    private fun postNotice(message: String) {
        ephemeral.value = ephemeral.value.copy(notice = message)
    }

    override fun onCleared() {
        container.llm.close()
        super.onCleared()
    }

    companion object {
        private const val MAX_KNOWLEDGE_CHARS = 5 * 1024 * 1024
    }
}
