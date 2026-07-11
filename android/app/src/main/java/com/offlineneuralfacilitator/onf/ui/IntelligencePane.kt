package com.offlineneuralfacilitator.onf.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.PrimaryScrollableTabRow
import androidx.compose.material3.Tab
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.offlineneuralfacilitator.onf.domain.model.ActionItem
import com.offlineneuralfacilitator.onf.domain.model.Decision
import com.offlineneuralfacilitator.onf.domain.model.Insight
import com.offlineneuralfacilitator.onf.domain.model.InsightKind
import com.offlineneuralfacilitator.onf.domain.model.OnfState
import com.offlineneuralfacilitator.onf.domain.model.Severity

internal enum class IntelligenceTab(val label: String) {
    GUIDANCE("Guidance"),
    DECISIONS("Decisions"),
    ACTIONS("Actions"),
    RISKS("Risks"),
}

@Composable
internal fun IntelligencePane(
    state: OnfState,
    modifier: Modifier = Modifier,
    initialTab: IntelligenceTab = IntelligenceTab.GUIDANCE,
) {
    var selected by rememberSaveable { mutableStateOf(initialTab) }
    Column(
        modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.surface),
    ) {
        Column(Modifier.padding(horizontal = 18.dp, vertical = 17.dp)) {
            SectionHeading(
                eyebrow = "Facilitator intelligence",
                title = when (selected) {
                    IntelligenceTab.GUIDANCE -> "Live guidance"
                    IntelligenceTab.DECISIONS -> "Decision record"
                    IntelligenceTab.ACTIONS -> "Owned next steps"
                    IntelligenceTab.RISKS -> "Risks and tension"
                },
                trailing = {
                    StatusPill(
                        text = "${state.insights.size} signals",
                        color = MaterialTheme.colorScheme.primary,
                    )
                },
            )
        }
        PrimaryScrollableTabRow(
            selectedTabIndex = selected.ordinal,
            edgePadding = 12.dp,
            containerColor = MaterialTheme.colorScheme.surface,
            divider = { HorizontalDivider(color = MaterialTheme.colorScheme.outline) },
        ) {
            IntelligenceTab.entries.forEach { tab ->
                val count = when (tab) {
                    IntelligenceTab.GUIDANCE -> state.insights.size
                    IntelligenceTab.DECISIONS -> state.decisions.size
                    IntelligenceTab.ACTIONS -> state.actions.size
                    IntelligenceTab.RISKS -> state.risks.size
                }
                Tab(
                    selected = selected == tab,
                    onClick = { selected = tab },
                    text = { Text("${tab.label}  $count", maxLines = 1) },
                )
            }
        }

        when (selected) {
            IntelligenceTab.GUIDANCE -> GuidanceList(state.insights, Modifier.weight(1f))
            IntelligenceTab.DECISIONS -> DecisionList(state.decisions, Modifier.weight(1f))
            IntelligenceTab.ACTIONS -> ActionList(state.actions, Modifier.weight(1f))
            IntelligenceTab.RISKS -> GuidanceList(state.risks, Modifier.weight(1f), emptyTitle = "No active risk signal")
        }
    }
}

@Composable
private fun GuidanceList(
    insights: List<Insight>,
    modifier: Modifier = Modifier,
    emptyTitle: String = "Waiting for the room",
) {
    if (insights.isEmpty()) {
        Box(modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            EmptyState(emptyTitle, "Guidance appears as the local facilitator detects evidence, pace, specialist skills, or diverging positions.")
        }
        return
    }
    LazyColumn(
        modifier = modifier,
        contentPadding = androidx.compose.foundation.layout.PaddingValues(14.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        items(insights.asReversed(), key = Insight::id) { InsightCard(it) }
    }
}

@Composable
private fun InsightCard(insight: Insight) {
    val signalColor = when (insight.severity) {
        Severity.HIGH -> MaterialTheme.colorScheme.error
        Severity.MEDIUM -> Color(0xFFD97706)
        Severity.LOW -> MaterialTheme.colorScheme.tertiary
        Severity.INFO -> when (insight.kind) {
            InsightKind.KNOWLEDGE -> MaterialTheme.colorScheme.secondary
            InsightKind.SKILL -> MaterialTheme.colorScheme.primary
            else -> MaterialTheme.colorScheme.onSurfaceVariant
        }
    }
    OnfCard(Modifier.fillMaxWidth()) {
        Column {
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                    Box(Modifier.size(9.dp).clip(RoundedCornerShape(100.dp)).background(signalColor))
                    Text(insight.title, style = MaterialTheme.typography.titleMedium)
                }
                Text(
                    insight.kind.name,
                    style = MaterialTheme.typography.labelLarge,
                    color = signalColor,
                    fontSize = 9.sp,
                )
            }
            Spacer(Modifier.height(9.dp))
            Text(insight.text, style = MaterialTheme.typography.bodyMedium)
            insight.citation?.let { citation ->
                Spacer(Modifier.height(10.dp))
                Text(
                    "SOURCE · $citation",
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.secondary,
                    fontSize = 9.sp,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                )
            }
        }
    }
}

@Composable
private fun DecisionList(decisions: List<Decision>, modifier: Modifier = Modifier) {
    if (decisions.isEmpty()) {
        Box(modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            EmptyState("No decision recorded", "Say “we have decided to…” or add a decision-oriented participant turn.")
        }
        return
    }
    LazyColumn(
        modifier,
        contentPadding = androidx.compose.foundation.layout.PaddingValues(14.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        items(decisions, key = Decision::id) { decision ->
            OnfCard(Modifier.fillMaxWidth()) {
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Box(
                        Modifier.size(30.dp).clip(RoundedCornerShape(10.dp)).background(MaterialTheme.colorScheme.primary.copy(alpha = 0.12f)),
                        contentAlignment = Alignment.Center,
                    ) { Text("✓", color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Black) }
                    Column(Modifier.weight(1f)) {
                        Text(decision.text, style = MaterialTheme.typography.titleMedium)
                        decision.rationale.takeIf(String::isNotBlank)?.let {
                            Spacer(Modifier.height(7.dp))
                            Text(it, color = MaterialTheme.colorScheme.onSurfaceVariant, style = MaterialTheme.typography.bodyMedium)
                        }
                        Spacer(Modifier.height(7.dp))
                        Text(formatClock(decision.timestampEpochMs), fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
        }
    }
}

@Composable
private fun ActionList(actions: List<ActionItem>, modifier: Modifier = Modifier) {
    if (actions.isEmpty()) {
        Box(modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            EmptyState("No owned action yet", "Use “Action item: Priya will…” to capture the work, owner, and due time deterministically.")
        }
        return
    }
    LazyColumn(
        modifier,
        contentPadding = androidx.compose.foundation.layout.PaddingValues(14.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        items(actions, key = ActionItem::id) { action ->
            OnfCard(Modifier.fillMaxWidth()) {
                Column {
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text(action.owner.uppercase(), style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary)
                        Text(action.due, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 10.sp)
                    }
                    Spacer(Modifier.height(9.dp))
                    Text(action.text, style = MaterialTheme.typography.titleMedium)
                    Spacer(Modifier.height(10.dp))
                    Box(
                        Modifier
                            .clip(RoundedCornerShape(100.dp))
                            .background(MaterialTheme.colorScheme.tertiary.copy(alpha = 0.10f))
                            .padding(horizontal = 9.dp, vertical = 4.dp),
                    ) {
                        Text("OPEN", color = MaterialTheme.colorScheme.tertiary, style = MaterialTheme.typography.labelLarge, fontSize = 9.sp)
                    }
                }
            }
        }
    }
}
