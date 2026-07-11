package com.offlineneuralfacilitator.onf.ui

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
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
import androidx.compose.ui.focus.FocusDirection
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.offlineneuralfacilitator.onf.ai.EnginePhase
import com.offlineneuralfacilitator.onf.domain.model.OnfState
import com.offlineneuralfacilitator.onf.domain.model.TranscriptMessage
import kotlin.math.sin

@Composable
internal fun TranscriptPane(
    state: OnfState,
    recording: com.offlineneuralfacilitator.onf.audio.RecordingState,
    llmReady: Boolean,
    busy: Boolean,
    onAddTurn: (String, String) -> Unit,
    onAsk: (String) -> Unit,
    onToggleRecording: () -> Unit,
    onTranscribeLatest: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val listState = rememberLazyListState()
    LaunchedEffect(state.transcript.size) {
        if (state.transcript.isNotEmpty()) listState.animateScrollToItem(state.transcript.lastIndex)
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background),
    ) {
        Column(Modifier.padding(horizontal = 20.dp, vertical = 17.dp)) {
            SectionHeading(
                eyebrow = if (recording.isRecording) "Capturing privately" else "Live workspace",
                title = state.session.topic,
                trailing = {
                    StatusPill(
                        if (recording.isRecording) "Recording" else "Ready",
                        color = if (recording.isRecording) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.tertiary,
                    )
                },
            )
            Spacer(Modifier.height(14.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                MetricTile(formatElapsed(state.metrics.durationSeconds), "elapsed", Modifier.weight(1f))
                MetricTile(state.metrics.turnCount.toString(), "turns", Modifier.weight(1f))
                MetricTile("${state.metrics.alignmentScore}%", "alignment", Modifier.weight(1f))
            }
        }
        HorizontalDivider(color = MaterialTheme.colorScheme.outline)

        if (state.transcript.isEmpty()) {
            Box(Modifier.weight(1f), contentAlignment = Alignment.Center) {
                EmptyState(
                    title = "The room is ready",
                    message = "Capture a participant turn, start encrypted audio, or run the Code Blue showcase.",
                )
            }
        } else {
            LazyColumn(
                modifier = Modifier.weight(1f),
                state = listState,
                verticalArrangement = Arrangement.spacedBy(10.dp),
                contentPadding = androidx.compose.foundation.layout.PaddingValues(16.dp),
            ) {
                items(state.transcript, key = TranscriptMessage::id) { message ->
                    TranscriptCard(message)
                }
            }
        }

        RecordingStrip(
            recording = recording,
            llmReady = llmReady,
            busy = busy,
            onToggleRecording = onToggleRecording,
            onTranscribeLatest = onTranscribeLatest,
        )
        Composer(
            enabled = !busy,
            onAddTurn = onAddTurn,
            onAsk = onAsk,
        )
    }
}

@Composable
private fun TranscriptCard(message: TranscriptMessage) {
    val assistant = message.role == "assistant"
    val user = message.role == "user"
    val accent = when {
        assistant -> MaterialTheme.colorScheme.primary
        user -> MaterialTheme.colorScheme.secondary
        else -> MaterialTheme.colorScheme.onSurfaceVariant
    }
    OnfCard(
        modifier = Modifier.fillMaxWidth(),
        padding = 0.dp,
    ) {
        Row(Modifier.fillMaxWidth()) {
            Box(Modifier.width(4.dp).fillMaxHeight().background(accent))
            Column(Modifier.padding(horizontal = 15.dp, vertical = 13.dp).weight(1f)) {
                Row(
                    Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                        Box(Modifier.size(7.dp).clip(RoundedCornerShape(100.dp)).background(accent))
                        Text(message.speaker, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                        if (assistant) Text("LOCAL AI", color = accent, style = MaterialTheme.typography.labelLarge, fontSize = 9.sp)
                    }
                    Text(formatClock(message.timestampEpochMs), color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 11.sp)
                }
                Spacer(Modifier.height(8.dp))
                Text(message.content, style = MaterialTheme.typography.bodyLarge)
            }
        }
    }
}

@Composable
private fun RecordingStrip(
    recording: com.offlineneuralfacilitator.onf.audio.RecordingState,
    llmReady: Boolean,
    busy: Boolean,
    onToggleRecording: () -> Unit,
    onTranscribeLatest: () -> Unit,
) {
    Column(
        Modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.55f))
            .padding(horizontal = 16.dp, vertical = 11.dp),
    ) {
        Row(
            Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Button(
                onClick = onToggleRecording,
                enabled = !busy,
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (recording.isRecording) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary,
                ),
            ) {
                Text(if (recording.isRecording) "STOP CAPTURE" else "START PRIVATE CAPTURE", style = MaterialTheme.typography.labelLarge)
            }
            Waveform(recording.isRecording, Modifier.weight(1f).height(28.dp))
            Column(horizontalAlignment = Alignment.End) {
                Text(
                    formatElapsed(recording.elapsedMs / 1_000),
                    fontWeight = FontWeight.Bold,
                    fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace,
                )
                Text(
                    "${recording.segmentCount} AES-GCM segments · ${compactBytes(recording.encryptedBytes)}",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    fontSize = 10.sp,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
        }
        AnimatedVisibility(visible = !recording.isRecording && recording.segmentCount > 0) {
            Row(
                Modifier.fillMaxWidth().padding(top = 8.dp),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onTranscribeLatest, enabled = llmReady && !busy) {
                    Text(if (llmReady) "Transcribe newest segment with Gemma" else "Load multimodal Gemma to transcribe")
                }
            }
        }
        recording.error?.let {
            Text(it, color = MaterialTheme.colorScheme.error, fontSize = 12.sp, modifier = Modifier.padding(top = 6.dp))
        }
    }
}

@Composable
private fun Waveform(active: Boolean, modifier: Modifier = Modifier) {
    val tick = remember(active) { System.nanoTime().toFloat() }
    Canvas(modifier.semantics { contentDescription = if (active) "Audio capture active" else "Audio capture stopped" }) {
        val count = 24
        val spacing = size.width / count
        repeat(count) { index ->
            val normalized = if (active) (0.35f + 0.65f * kotlin.math.abs(sin(tick + index * 0.73f))) else 0.22f
            val height = size.height * normalized
            val x = spacing * index + spacing / 2
            drawLine(
                color = if (active) Color(0xFFDC2626) else Color.Gray.copy(alpha = 0.45f),
                start = androidx.compose.ui.geometry.Offset(x, (size.height - height) / 2),
                end = androidx.compose.ui.geometry.Offset(x, (size.height + height) / 2),
                strokeWidth = 2.dp.toPx(),
                cap = StrokeCap.Round,
            )
        }
    }
}

@Composable
private fun Composer(
    enabled: Boolean,
    onAddTurn: (String, String) -> Unit,
    onAsk: (String) -> Unit,
) {
    var askMode by rememberSaveable { mutableStateOf(false) }
    var text by rememberSaveable { mutableStateOf("") }
    var speaker by rememberSaveable { mutableStateOf("Speaker") }
    val focus = LocalFocusManager.current

    Column(
        Modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.surface)
            .padding(14.dp),
    ) {
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            FilterChip(selected = !askMode, onClick = { askMode = false }, label = { Text("Capture turn") })
            FilterChip(selected = askMode, onClick = { askMode = true }, label = { Text("Ask ONF") })
        }
        Spacer(Modifier.height(8.dp))
        AnimatedVisibility(!askMode) {
            OutlinedTextField(
                value = speaker,
                onValueChange = { speaker = it.take(60) },
                label = { Text("Speaker") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                enabled = enabled,
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Next),
                keyboardActions = KeyboardActions(onNext = { focus.moveFocus(FocusDirection.Down) }),
            )
        }
        Spacer(Modifier.height(8.dp))
        Row(
            Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(10.dp),
            verticalAlignment = Alignment.Bottom,
        ) {
            OutlinedTextField(
                value = text,
                onValueChange = { text = it.take(4_000) },
                label = { Text(if (askMode) "Question for the local facilitator" else "What was said") },
                placeholder = { Text(if (askMode) "What decision did we record?" else "Capture a complete participant turn…") },
                modifier = Modifier.weight(1f),
                minLines = 2,
                maxLines = 5,
                enabled = enabled,
            )
            Button(
                onClick = {
                    val clean = text.trim()
                    if (clean.isNotEmpty()) {
                        if (askMode) onAsk(clean) else onAddTurn(clean, speaker.trim())
                        text = ""
                        focus.clearFocus()
                    }
                },
                enabled = enabled && text.isNotBlank(),
                modifier = Modifier.height(56.dp),
            ) {
                Text(if (askMode) "ASK" else "ADD", style = MaterialTheme.typography.labelLarge)
            }
        }
    }
}
