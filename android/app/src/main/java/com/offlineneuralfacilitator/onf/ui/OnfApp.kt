package com.offlineneuralfacilitator.onf.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.VerticalDivider
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.offlineneuralfacilitator.onf.ai.EnginePhase

private enum class MobilePane(val label: String) {
    ROOM("Room"),
    GUIDANCE("Guidance"),
    OUTCOMES("Outcomes"),
}

@Composable
fun OnfApp(
    viewModel: MainViewModel,
    onRequestRecording: () -> Unit,
    onImportModel: () -> Unit,
    onImportKnowledge: () -> Unit,
    onExport: (String) -> Unit,
    onOpenFoundryCompanion: () -> Unit,
    onRequestFoundrySdk: () -> Unit,
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val snackbar = remember { SnackbarHostState() }
    var showSystem by rememberSaveable { mutableStateOf(false) }
    var showNewSession by rememberSaveable { mutableStateOf(false) }
    var mobilePane by rememberSaveable { mutableStateOf(MobilePane.ROOM) }

    LaunchedEffect(uiState.notice) {
        uiState.notice?.let {
            snackbar.showSnackbar(it)
            viewModel.clearNotice()
        }
    }

    Box(
        Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .safeDrawingPadding(),
    ) {
        Scaffold(
            containerColor = MaterialTheme.colorScheme.background,
            snackbarHost = { SnackbarHost(snackbar) },
            topBar = {
                OnfTopBar(
                    uiState = uiState,
                    onNewSession = { showNewSession = true },
                    onRunShowcase = viewModel::runShowcase,
                    onOpenSystem = { showSystem = true },
                    onExport = onExport,
                )
            },
        ) { padding ->
            if (!uiState.initialized) {
                LoadingWorkspace(Modifier.padding(padding))
            } else {
                BoxWithConstraints(
                    Modifier
                        .padding(padding)
                        .fillMaxSize(),
                ) {
                    when {
                        maxWidth >= 1_050.dp -> {
                            Row(Modifier.fillMaxSize()) {
                                SessionRail(
                                    uiState,
                                    onNewSession = { showNewSession = true },
                                    onRunShowcase = viewModel::runShowcase,
                                    onOpenSystem = { showSystem = true },
                                    modifier = Modifier.width(252.dp).fillMaxHeight(),
                                )
                                VerticalDivider(color = MaterialTheme.colorScheme.outline)
                                TranscriptPane(
                                    state = uiState.session,
                                    recording = uiState.recording,
                                    llmReady = uiState.llm.phase == EnginePhase.READY,
                                    busy = uiState.busyLabel != null,
                                    onAddTurn = viewModel::addTurn,
                                    onAsk = viewModel::ask,
                                    onToggleRecording = {
                                        if (uiState.recording.isRecording) viewModel.stopRecording() else onRequestRecording()
                                    },
                                    onTranscribeLatest = viewModel::transcribeLatestAudio,
                                    modifier = Modifier.weight(1.25f),
                                )
                                VerticalDivider(color = MaterialTheme.colorScheme.outline)
                                IntelligencePane(uiState.session, Modifier.weight(0.92f))
                            }
                        }
                        maxWidth >= 700.dp -> {
                            Row(Modifier.fillMaxSize()) {
                                TranscriptPane(
                                    state = uiState.session,
                                    recording = uiState.recording,
                                    llmReady = uiState.llm.phase == EnginePhase.READY,
                                    busy = uiState.busyLabel != null,
                                    onAddTurn = viewModel::addTurn,
                                    onAsk = viewModel::ask,
                                    onToggleRecording = {
                                        if (uiState.recording.isRecording) viewModel.stopRecording() else onRequestRecording()
                                    },
                                    onTranscribeLatest = viewModel::transcribeLatestAudio,
                                    modifier = Modifier.weight(1.12f),
                                )
                                VerticalDivider(color = MaterialTheme.colorScheme.outline)
                                IntelligencePane(uiState.session, Modifier.weight(0.88f))
                            }
                        }
                        else -> {
                            Column(Modifier.fillMaxSize()) {
                                Box(Modifier.weight(1f)) {
                                    when (mobilePane) {
                                        MobilePane.ROOM -> TranscriptPane(
                                            state = uiState.session,
                                            recording = uiState.recording,
                                            llmReady = uiState.llm.phase == EnginePhase.READY,
                                            busy = uiState.busyLabel != null,
                                            onAddTurn = viewModel::addTurn,
                                            onAsk = viewModel::ask,
                                            onToggleRecording = {
                                                if (uiState.recording.isRecording) viewModel.stopRecording() else onRequestRecording()
                                            },
                                            onTranscribeLatest = viewModel::transcribeLatestAudio,
                                        )
                                        MobilePane.GUIDANCE -> IntelligencePane(uiState.session, initialTab = IntelligenceTab.GUIDANCE)
                                        MobilePane.OUTCOMES -> IntelligencePane(
                                            uiState.session,
                                            initialTab = if (uiState.session.decisions.isNotEmpty()) IntelligenceTab.DECISIONS else IntelligenceTab.ACTIONS,
                                        )
                                    }
                                }
                                MobileNavigation(mobilePane, onSelect = { mobilePane = it })
                            }
                        }
                    }
                }
            }
        }

        uiState.busyLabel?.let { BusyOverlay(it, uiState.modelImportProgress) }
    }

    if (showNewSession) {
        NewSessionDialog(
            onDismiss = { showNewSession = false },
            onCreate = viewModel::newSession,
        )
    }
    if (showSystem) {
        SystemSheet(
            uiState = uiState,
            onDismiss = { showSystem = false },
            onImportModel = onImportModel,
            onImportKnowledge = onImportKnowledge,
            onSelectModel = viewModel::selectModel,
            onRemoveModel = viewModel::removeModel,
            onOpenFoundryCompanion = onOpenFoundryCompanion,
            onRequestFoundrySdk = onRequestFoundrySdk,
        )
    }
}

@Composable
private fun OnfTopBar(
    uiState: MainUiState,
    onNewSession: () -> Unit,
    onRunShowcase: () -> Unit,
    onOpenSystem: () -> Unit,
    onExport: (String) -> Unit,
) {
    var exportMenu by remember { mutableStateOf(false) }
    var compactMenu by remember { mutableStateOf(false) }
    Surface(
        color = MaterialTheme.colorScheme.surface,
        shadowElevation = 2.dp,
        border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outline),
    ) {
        BoxWithConstraints {
            val compact = maxWidth < 760.dp
            Row(
                Modifier.fillMaxWidth().height(70.dp).padding(horizontal = if (compact) 10.dp else 16.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(if (compact) 8.dp else 12.dp),
            ) {
                BrandMark()
                Column(Modifier.weight(1f)) {
                    Text("OFFLINE NEURAL FACILITATOR", fontWeight = FontWeight.Black, letterSpacing = 1.2.sp, fontSize = if (compact) 11.sp else 13.sp)
                    Text(
                        uiState.session.session.topic,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        fontSize = 11.sp,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
                if (!compact) {
                    StatusPill("Device local")
                    Box {
                        TextButton(onClick = { exportMenu = true }) { Text("EXPORT") }
                        DropdownMenu(expanded = exportMenu, onDismissRequest = { exportMenu = false }) {
                            DropdownMenuItem(
                                text = { Text("Structured JSON") },
                                onClick = { exportMenu = false; onExport("json") },
                            )
                            DropdownMenuItem(
                                text = { Text("Meeting Markdown") },
                                onClick = { exportMenu = false; onExport("markdown") },
                            )
                        }
                    }
                    TextButton(onClick = onNewSession) { Text("NEW") }
                    TextButton(onClick = onRunShowcase, enabled = uiState.busyLabel == null) { Text("SHOWCASE") }
                    OutlinedButton(onClick = onOpenSystem) { Text("SYSTEM") }
                } else {
                    Box {
                        OutlinedButton(onClick = { compactMenu = true }) { Text("MENU") }
                        DropdownMenu(expanded = compactMenu, onDismissRequest = { compactMenu = false }) {
                            DropdownMenuItem(text = { Text("New private session") }, onClick = { compactMenu = false; onNewSession() })
                            DropdownMenuItem(text = { Text("Run Code Blue showcase") }, onClick = { compactMenu = false; onRunShowcase() })
                            DropdownMenuItem(text = { Text("Export structured JSON") }, onClick = { compactMenu = false; onExport("json") })
                            DropdownMenuItem(text = { Text("Export meeting Markdown") }, onClick = { compactMenu = false; onExport("markdown") })
                            DropdownMenuItem(text = { Text("Private system and models") }, onClick = { compactMenu = false; onOpenSystem() })
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun SessionRail(
    uiState: MainUiState,
    onNewSession: () -> Unit,
    onRunShowcase: () -> Unit,
    onOpenSystem: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier
            .background(MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.42f))
            .padding(16.dp),
    ) {
        Text("PRIVATE WORKSPACE", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Spacer(Modifier.height(5.dp))
        Text(uiState.session.session.id, fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Spacer(Modifier.height(18.dp))
        Button(onClick = onNewSession, modifier = Modifier.fillMaxWidth()) { Text("NEW SESSION") }
        Spacer(Modifier.height(8.dp))
        OutlinedButton(onClick = onRunShowcase, modifier = Modifier.fillMaxWidth()) { Text("RUN CODE BLUE") }
        Spacer(Modifier.height(20.dp))

        OnfCard(Modifier.fillMaxWidth(), padding = 14.dp) {
            Column {
                Text("LOCAL CAPABILITIES", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary)
                Spacer(Modifier.height(12.dp))
                CapabilityRow("Knowledge", "${uiState.knowledgeCount} chunks")
                CapabilityRow("Skills", "5 active-ready")
                CapabilityRow("Audio", "AES-GCM")
                CapabilityRow(
                    "Gemma",
                    when (uiState.llm.phase) {
                        EnginePhase.READY -> uiState.llm.backend ?: "ready"
                        EnginePhase.LOADING -> "loading"
                        EnginePhase.ERROR -> "attention"
                        EnginePhase.UNCONFIGURED -> "not loaded"
                    },
                )
            }
        }
        Spacer(Modifier.height(12.dp))
        OnfCard(Modifier.fillMaxWidth(), padding = 14.dp) {
            Column {
                Text("ALIGNMENT", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Spacer(Modifier.height(7.dp))
                Text("${uiState.session.metrics.alignmentScore}%", fontSize = 34.sp, fontWeight = FontWeight.Black)
                Text("Based on owned actions, explicit decisions, and active risk signals.", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 11.sp)
            }
        }
        Spacer(Modifier.weight(1f))
        Column(
            Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(14.dp))
                .background(MaterialTheme.colorScheme.tertiary.copy(alpha = 0.09f))
                .padding(13.dp),
        ) {
            Text("ZERO NETWORK SCOPE", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.tertiary, fontSize = 9.sp)
            Spacer(Modifier.height(5.dp))
            Text("No internet permission. No telemetry. No cloud backup.", fontSize = 11.sp)
        }
        TextButton(onClick = onOpenSystem, modifier = Modifier.fillMaxWidth()) { Text("VIEW PRIVATE SYSTEM") }
    }
}

@Composable
private fun CapabilityRow(label: String, value: String) {
    Row(Modifier.fillMaxWidth().padding(vertical = 5.dp), horizontalArrangement = Arrangement.SpaceBetween) {
        Text(label, fontSize = 12.sp)
        Text(value, fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun MobileNavigation(selected: MobilePane, onSelect: (MobilePane) -> Unit) {
    Surface(color = MaterialTheme.colorScheme.surface, shadowElevation = 8.dp) {
        Row(Modifier.fillMaxWidth().padding(horizontal = 8.dp, vertical = 7.dp)) {
            MobilePane.entries.forEach { pane ->
                val active = selected == pane
                TextButton(
                    onClick = { onSelect(pane) },
                    modifier = Modifier.weight(1f),
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Box(
                            Modifier
                                .size(width = 28.dp, height = 3.dp)
                                .clip(RoundedCornerShape(100.dp))
                                .background(if (active) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surface),
                        )
                        Spacer(Modifier.height(5.dp))
                        Text(pane.label, color = if (active) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
        }
    }
}

@Composable
private fun LoadingWorkspace(modifier: Modifier = Modifier) {
    Column(
        modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        BrandMark(Modifier.size(58.dp))
        Spacer(Modifier.height(18.dp))
        Text("Preparing private workspace", style = MaterialTheme.typography.headlineSmall)
        Spacer(Modifier.height(12.dp))
        CircularProgressIndicator()
    }
}

@Composable
private fun BusyOverlay(label: String, progress: Float?) {
    Box(
        Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.scrim.copy(alpha = 0.36f)),
        contentAlignment = Alignment.Center,
    ) {
        OnfCard(Modifier.width(290.dp)) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                if (progress == null) {
                    CircularProgressIndicator()
                } else {
                    CircularProgressIndicator(progress = { progress })
                }
                Spacer(Modifier.height(14.dp))
                Text(label, fontWeight = FontWeight.Bold)
                Spacer(Modifier.height(5.dp))
                Text("Processing remains on this device", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 11.sp)
            }
        }
    }
}
