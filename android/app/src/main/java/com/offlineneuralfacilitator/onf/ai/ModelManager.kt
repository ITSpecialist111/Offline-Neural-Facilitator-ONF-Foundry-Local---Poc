package com.offlineneuralfacilitator.onf.ai

import android.content.Context
import android.net.Uri
import android.os.storage.StorageManager
import android.provider.OpenableColumns
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File

data class ModelDescriptor(
    val name: String,
    val path: String,
    val sizeBytes: Long,
)

internal class ModelManager(
    private val context: Context,
    preferencesName: String = PREFERENCES,
    modelDirectory: File = File(context.filesDir, "models"),
) {
    private val preferences = context.getSharedPreferences(preferencesName, Context.MODE_PRIVATE)
    private val modelDirectory = modelDirectory.apply(File::mkdirs)

    fun selected(): ModelDescriptor? {
        val path = preferences.getString(KEY_PATH, null) ?: return null
        val file = File(path).takeIf(File::isFile) ?: return null
        return ModelDescriptor(
            name = preferences.getString(KEY_NAME, null) ?: file.name,
            path = file.absolutePath,
            sizeBytes = file.length(),
        )
    }

    fun available(): List<ModelDescriptor> {
        val selected = selected()
        return modelDirectory.listFiles { file ->
            file.isFile && file.extension.equals("litertlm", ignoreCase = true)
        }.orEmpty()
            .map { file ->
                ModelDescriptor(
                    name = if (file.absolutePath == selected?.path) {
                        selected.name
                    } else {
                        friendlyName(file.name)
                    },
                    path = file.absolutePath,
                    sizeBytes = file.length(),
                )
            }
            .sortedWith(
                compareByDescending<ModelDescriptor> { it.path == selected?.path }
                    .thenBy { it.name.lowercase() },
            )
    }

    suspend fun import(
        uri: Uri,
        onProgress: (Float) -> Unit = {},
    ): ModelDescriptor = withContext(Dispatchers.IO) {
        val resolver = context.contentResolver
        val metadata = resolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE), null, null, null)
            ?.use { cursor ->
                if (!cursor.moveToFirst()) null else {
                    val name = cursor.getString(cursor.getColumnIndexOrThrow(OpenableColumns.DISPLAY_NAME))
                    val sizeIndex = cursor.getColumnIndex(OpenableColumns.SIZE)
                    name to if (sizeIndex >= 0 && !cursor.isNull(sizeIndex)) cursor.getLong(sizeIndex) else -1L
                }
            }
        val displayName = metadata?.first?.takeIf { it.endsWith(".litertlm", ignoreCase = true) }
            ?: throw IllegalArgumentException("Select a .litertlm model pack.")
        val declaredSize = metadata.second
        if (declaredSize > 0) {
            val storage = context.getSystemService(StorageManager::class.java)
            val volume = storage.getUuidForPath(context.filesDir)
            if (storage.getAllocatableBytes(volume) < declaredSize + RESERVE_BYTES) {
                throw IllegalStateException("Not enough private storage for this model and its runtime cache.")
            }
        }

        val safeBase = displayName.substringBeforeLast('.').replace(Regex("[^A-Za-z0-9_-]"), "_")
        val destination = File(modelDirectory, "$safeBase-${System.currentTimeMillis()}.litertlm")
        val temporary = File(modelDirectory, "${destination.name}.importing")
        temporary.delete()
        try {
            resolver.openInputStream(uri)?.use { source ->
                temporary.outputStream().buffered(BUFFER_SIZE).use { target ->
                    val buffer = ByteArray(BUFFER_SIZE)
                    var copied = 0L
                    while (true) {
                        val count = source.read(buffer)
                        if (count < 0) break
                        target.write(buffer, 0, count)
                        copied += count
                        if (declaredSize > 0) onProgress((copied.toFloat() / declaredSize).coerceIn(0f, 1f))
                    }
                }
            } ?: throw IllegalArgumentException("The selected model could not be opened.")

            require(declaredSize <= 0 || temporary.length() == declaredSize) {
                "The model copy was incomplete. Expected $declaredSize bytes but received ${temporary.length()}."
            }
            require(temporary.length() >= MIN_MODEL_BYTES) { "The selected file is too small to be a LiteRT-LM model." }
            check(temporary.renameTo(destination)) { "The imported model could not be finalized." }
        } catch (error: Throwable) {
            temporary.delete()
            destination.delete()
            throw error
        }
        onProgress(1f)
        ModelDescriptor(displayName, destination.absolutePath, destination.length())
    }

    fun select(descriptor: ModelDescriptor) {
        require(File(descriptor.path).isFile) { "The selected model is no longer available." }
        preferences.edit()
            .putString(KEY_PATH, descriptor.path)
            .putString(KEY_NAME, descriptor.name)
            .apply()
    }

    fun discard(descriptor: ModelDescriptor) {
        if (selected()?.path != descriptor.path) File(descriptor.path).delete()
    }

    fun remove(descriptor: ModelDescriptor): Boolean {
        if (selected()?.path == descriptor.path) return false
        return File(descriptor.path).delete()
    }

    private fun friendlyName(filename: String): String = filename
        .replace(Regex("-\\d{13}(?=\\.litertlm$)", RegexOption.IGNORE_CASE), "")

    companion object {
        private const val PREFERENCES = "onf_models"
        private const val KEY_PATH = "selected_path"
        private const val KEY_NAME = "selected_name"
        private const val BUFFER_SIZE = 8 * 1024 * 1024
        private const val MIN_MODEL_BYTES = 10L * 1024 * 1024
        private const val RESERVE_BYTES = 512L * 1024 * 1024
    }
}
