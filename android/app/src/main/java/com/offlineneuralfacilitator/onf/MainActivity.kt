package com.offlineneuralfacilitator.onf

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.core.content.ContextCompat
import androidx.lifecycle.viewmodel.compose.viewModel
import com.offlineneuralfacilitator.onf.ui.ExportPayload
import com.offlineneuralfacilitator.onf.ui.MainViewModel
import com.offlineneuralfacilitator.onf.ui.OnfApp
import com.offlineneuralfacilitator.onf.ui.theme.OnfTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            OnfTheme {
                val viewModel: MainViewModel = viewModel()
                var pendingJson by remember { mutableStateOf<ExportPayload?>(null) }
                var pendingMarkdown by remember { mutableStateOf<ExportPayload?>(null) }

                val permissionLauncher = rememberLauncherForActivityResult(
                    ActivityResultContracts.RequestMultiplePermissions(),
                ) { result ->
                    if (result[Manifest.permission.RECORD_AUDIO] == true) {
                        viewModel.startRecording()
                    } else {
                        viewModel.reportNotice("Microphone permission is required for private audio capture.")
                    }
                }
                val modelPicker = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
                    uri?.let(viewModel::importModel)
                }
                val knowledgePicker = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
                    uri?.let(viewModel::importKnowledge)
                }
                val jsonExporter = rememberLauncherForActivityResult(
                    ActivityResultContracts.CreateDocument("application/json"),
                ) { uri ->
                    val payload = pendingJson
                    if (uri != null && payload != null) {
                        runCatching {
                            contentResolver.openOutputStream(uri, "w")?.use { it.write(payload.bytes) }
                                ?: error("The export destination could not be opened.")
                        }.onSuccess {
                            viewModel.reportNotice("Structured session exported locally")
                        }.onFailure { viewModel.reportNotice("Export failed: ${it.message}") }
                    }
                    pendingJson = null
                }
                val markdownExporter = rememberLauncherForActivityResult(
                    ActivityResultContracts.CreateDocument("text/markdown"),
                ) { uri ->
                    val payload = pendingMarkdown
                    if (uri != null && payload != null) {
                        runCatching {
                            contentResolver.openOutputStream(uri, "w")?.use { it.write(payload.bytes) }
                                ?: error("The export destination could not be opened.")
                        }.onSuccess {
                            viewModel.reportNotice("Meeting record exported locally")
                        }.onFailure { viewModel.reportNotice("Export failed: ${it.message}") }
                    }
                    pendingMarkdown = null
                }

                OnfApp(
                    viewModel = viewModel,
                    onRequestRecording = {
                        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
                            viewModel.startRecording()
                        } else {
                            val permissions = buildList {
                                add(Manifest.permission.RECORD_AUDIO)
                                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) add(Manifest.permission.POST_NOTIFICATIONS)
                            }.toTypedArray()
                            permissionLauncher.launch(permissions)
                        }
                    },
                    onImportModel = { modelPicker.launch(arrayOf("application/octet-stream", "*/*")) },
                    onImportKnowledge = { knowledgePicker.launch(arrayOf("text/markdown", "text/plain")) },
                    onExport = { kind ->
                        val payload = viewModel.export(kind)
                        if (kind == "json") {
                            pendingJson = payload
                            jsonExporter.launch(payload.filename)
                        } else {
                            pendingMarkdown = payload
                            markdownExporter.launch(payload.filename)
                        }
                    },
                )
            }
        }
    }
}
