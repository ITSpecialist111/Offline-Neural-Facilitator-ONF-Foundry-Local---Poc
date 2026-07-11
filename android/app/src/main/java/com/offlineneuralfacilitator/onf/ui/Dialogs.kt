package com.offlineneuralfacilitator.onf.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.offlineneuralfacilitator.onf.ai.EnginePhase

@Composable
internal fun NewSessionDialog(
    onDismiss: () -> Unit,
    onCreate: (String) -> Unit,
) {
    var topic by remember { mutableStateOf("") }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Open a private workspace") },
        text = {
            Column {
                Text(
                    "The new session is stored only in this app's private device storage.",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Spacer(Modifier.height(14.dp))
                OutlinedTextField(
                    value = topic,
                    onValueChange = { topic = it.take(120) },
                    label = { Text("Session topic (optional)") },
                    placeholder = { Text("Derived automatically after two turns") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
            }
        },
        confirmButton = {
            Button(onClick = { onCreate(topic.trim()); onDismiss() }) { Text("CREATE") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } },
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun SystemSheet(
    uiState: MainUiState,
    onDismiss: () -> Unit,
    onImportModel: () -> Unit,
    onImportKnowledge: () -> Unit,
    onSelectModel: (String) -> Unit,
    onRemoveModel: (String) -> Unit,
    onOpenFoundryCompanion: () -> Unit,
    onRequestFoundrySdk: () -> Unit,
) {
    ModalBottomSheet(onDismissRequest = onDismiss) {
        Column(
            Modifier
                .fillMaxWidth()
                .verticalScroll(rememberScrollState())
                .navigationBarsPadding()
                .padding(horizontal = 22.dp, vertical = 8.dp),
        ) {
            SectionHeading("Device runtime", "Private system")
            Spacer(Modifier.height(18.dp))
            OnfCard(Modifier.fillMaxWidth()) {
                Column {
                    Row(
                        Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Column(Modifier.weight(1f)) {
                            Text("Microsoft Foundry Local", fontWeight = FontWeight.Bold)
                            Text(
                                uiState.foundryCompanion.summary,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                fontSize = 12.sp,
                            )
                        }
                        StatusPill(
                            if (uiState.foundryCompanion.installed) "Preview found" else "Optional",
                            color = if (uiState.foundryCompanion.installed) {
                                MaterialTheme.colorScheme.tertiary
                            } else {
                                MaterialTheme.colorScheme.onSurfaceVariant
                            },
                        )
                    }
                    Spacer(Modifier.height(10.dp))
                    Text(
                        if (uiState.foundryCompanion.installed) {
                            "The official companion service is available but not connected. ONF retains LiteRT-LM until the gated Android SDK is linked; undocumented IPC is not used. The preview companion has separate network and data terms."
                        } else {
                            "Install the official preview companion and obtain the gated Android SDK to enable a future Foundry-backed engine."
                        },
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        style = MaterialTheme.typography.bodyMedium,
                    )
                    Spacer(Modifier.height(12.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        if (uiState.foundryCompanion.installed) {
                            OutlinedButton(onClick = onOpenFoundryCompanion) {
                                Text("OPEN COMPANION")
                            }
                        }
                        TextButton(onClick = onRequestFoundrySdk) {
                            Text("REQUEST SDK ACCESS")
                        }
                    }
                }
            }

            Spacer(Modifier.height(12.dp))
            OnfCard(Modifier.fillMaxWidth()) {
                Column {
                    Text("Existing mobile model library", fontWeight = FontWeight.Bold)
                    Spacer(Modifier.height(5.dp))
                    Text(
                        uiState.gallery.summary,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        fontSize = 12.sp,
                    )
                    Spacer(Modifier.height(9.dp))
                    Text(
                        if (uiState.gallery.installed) {
                            "Gallery-downloaded models are isolated in Gallery's Android sandbox. ONF cannot reuse them in place; import the same $MODEL_PACK_EXTENSION file, or use development-only ADB provisioning."
                        } else {
                            "ONF can retain multiple compatible $MODEL_PACK_EXTENSION packs in its own private model library."
                        },
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
            }

            Spacer(Modifier.height(12.dp))
            OnfCard(Modifier.fillMaxWidth()) {
                Column {
                    Row(
                        Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Column(Modifier.weight(1f)) {
                            Text("Gemma 4 · LiteRT-LM", fontWeight = FontWeight.Bold)
                            Text(
                                uiState.llm.modelName ?: "No model imported",
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                fontSize = 12.sp,
                            )
                        }
                        StatusPill(
                            when (uiState.llm.phase) {
                                EnginePhase.READY -> uiState.llm.backend ?: "Ready"
                                EnginePhase.LOADING -> "Loading"
                                EnginePhase.ERROR -> "Attention"
                                EnginePhase.UNCONFIGURED -> "Optional"
                            },
                            color = when (uiState.llm.phase) {
                                EnginePhase.READY -> MaterialTheme.colorScheme.tertiary
                                EnginePhase.ERROR -> MaterialTheme.colorScheme.error
                                else -> MaterialTheme.colorScheme.primary
                            },
                        )
                    }
                    Spacer(Modifier.height(11.dp))
                    Text(uiState.llm.message, color = MaterialTheme.colorScheme.onSurfaceVariant, style = MaterialTheme.typography.bodyMedium)
                    if (uiState.deviceModels.isEmpty()) {
                        Spacer(Modifier.height(12.dp))
                        Text(
                            "No private model packs are installed in ONF.",
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            style = MaterialTheme.typography.bodyMedium,
                        )
                    } else {
                        Spacer(Modifier.height(12.dp))
                        Text(
                            "ONF PRIVATE MODEL LIBRARY",
                            style = MaterialTheme.typography.labelLarge,
                            color = MaterialTheme.colorScheme.primary,
                            fontSize = 9.sp,
                        )
                        uiState.deviceModels.forEachIndexed { index, model ->
                            if (index > 0) {
                                HorizontalDivider(
                                    modifier = Modifier.padding(vertical = 10.dp),
                                    color = MaterialTheme.colorScheme.outline,
                                )
                            } else {
                                Spacer(Modifier.height(8.dp))
                            }
                            val active = model.path == uiState.selectedModelPath
                            Row(
                                Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                Column(Modifier.weight(1f)) {
                                    Text(model.name, fontWeight = FontWeight.SemiBold, fontSize = 13.sp)
                                    Text(
                                        "${compactBytes(model.sizeBytes)}${if (active) " · active" else ""}",
                                        color = if (active) MaterialTheme.colorScheme.tertiary else MaterialTheme.colorScheme.onSurfaceVariant,
                                        fontSize = 11.sp,
                                    )
                                }
                                if (active) {
                                    StatusPill("Active")
                                } else {
                                    TextButton(
                                        onClick = { onSelectModel(model.path) },
                                        enabled = uiState.busyLabel == null,
                                    ) {
                                        Text("LOAD")
                                    }
                                    TextButton(
                                        onClick = { onRemoveModel(model.path) },
                                        enabled = uiState.busyLabel == null,
                                    ) {
                                        Text("REMOVE", color = MaterialTheme.colorScheme.error)
                                    }
                                }
                            }
                        }
                    }
                    uiState.modelImportProgress?.let { progress ->
                        Spacer(Modifier.height(12.dp))
                        LinearProgressIndicator(
                            progress = { progress },
                            modifier = Modifier.fillMaxWidth(),
                        )
                        Text("${(progress * 100).toInt()}% copied into private storage", fontSize = 10.sp)
                    }
                    Spacer(Modifier.height(14.dp))
                    Button(onClick = onImportModel, enabled = uiState.busyLabel == null) {
                        Text(if (uiState.deviceModels.isEmpty()) "IMPORT GEMMA MODEL" else "IMPORT ANOTHER MODEL")
                    }
                    Spacer(Modifier.height(7.dp))
                    Text(
                        "Gemma 4 E2B is about 2.58 GB; E4B is about 3.65 GB. The model is not bundled in the APK.",
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        fontSize = 11.sp,
                    )
                }
            }

            Spacer(Modifier.height(12.dp))
            OnfCard(Modifier.fillMaxWidth()) {
                Column {
                    Text("Local knowledge vault", fontWeight = FontWeight.Bold)
                    Spacer(Modifier.height(5.dp))
                    Text(
                        "${uiState.knowledgeCount} section-aware chunks · deterministic 384D retrieval",
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        fontSize = 12.sp,
                    )
                    Spacer(Modifier.height(12.dp))
                    OutlinedButton(onClick = onImportKnowledge, enabled = uiState.busyLabel == null) {
                        Text("IMPORT MARKDOWN OR TEXT")
                    }
                }
            }

            Spacer(Modifier.height(18.dp))
            HorizontalDivider(color = MaterialTheme.colorScheme.outline)
            Spacer(Modifier.height(18.dp))
            Text("PRIVACY BOUNDARY", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary)
            Spacer(Modifier.height(10.dp))
            PrivacyFact("No internet permission", "The installed app cannot open network sockets.")
            PrivacyFact("Encrypted capture", "Five-second WAV segments use independent AES-256-GCM envelopes and a non-exportable Android Keystore key.")
            PrivacyFact("No cloud backup", "Sessions, models, the knowledge vault, and audio are excluded from Android backup and device transfer.")
            PrivacyFact("Model-local reasoning", "LiteRT-LM executes imported Gemma weights with GPU-first and CPU fallback on this device.")
            Spacer(Modifier.height(12.dp))
        }
    }
}

@Composable
private fun PrivacyFact(title: String, detail: String) {
    Row(
        Modifier
            .fillMaxWidth()
            .padding(vertical = 7.dp),
        horizontalArrangement = Arrangement.spacedBy(11.dp),
    ) {
        Text("✓", color = MaterialTheme.colorScheme.tertiary, fontWeight = FontWeight.Black)
        Column {
            Text(title, fontWeight = FontWeight.SemiBold)
            Text(detail, color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 12.sp)
        }
    }
}

private const val MODEL_PACK_EXTENSION = ".litertlm"
