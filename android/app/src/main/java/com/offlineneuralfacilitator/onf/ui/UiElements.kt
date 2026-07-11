package com.offlineneuralfacilitator.onf.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

@Composable
internal fun OnfCard(
    modifier: Modifier = Modifier,
    padding: Dp = 16.dp,
    content: @Composable () -> Unit,
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(18.dp),
        color = MaterialTheme.colorScheme.surface,
        tonalElevation = 0.dp,
        shadowElevation = 1.dp,
        border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outline),
    ) {
        Box(Modifier.padding(padding)) { content() }
    }
}

@Composable
internal fun BrandMark(modifier: Modifier = Modifier) {
    Box(
        modifier = modifier
            .size(38.dp)
            .clip(RoundedCornerShape(11.dp))
            .background(MaterialTheme.colorScheme.primary)
            .semantics { contentDescription = "ONF" },
        contentAlignment = Alignment.Center,
    ) {
        Canvas(Modifier.size(21.dp)) {
            val barWidth = 3.dp.toPx()
            val gap = 4.dp.toPx()
            val heights = listOf(9.dp.toPx(), 19.dp.toPx(), 13.dp.toPx())
            val startX = (size.width - (barWidth * 3 + gap * 2)) / 2
            heights.forEachIndexed { index, height ->
                val x = startX + index * (barWidth + gap)
                drawLine(
                    color = Color.White,
                    start = androidx.compose.ui.geometry.Offset(x + barWidth / 2, (size.height - height) / 2),
                    end = androidx.compose.ui.geometry.Offset(x + barWidth / 2, (size.height + height) / 2),
                    strokeWidth = barWidth,
                    cap = StrokeCap.Round,
                )
            }
        }
    }
}

@Composable
internal fun StatusPill(
    text: String,
    modifier: Modifier = Modifier,
    color: Color = MaterialTheme.colorScheme.tertiary,
) {
    Row(
        modifier = modifier
            .clip(RoundedCornerShape(100.dp))
            .background(color.copy(alpha = 0.10f))
            .border(1.dp, color.copy(alpha = 0.35f), RoundedCornerShape(100.dp))
            .padding(horizontal = 10.dp, vertical = 6.dp),
        horizontalArrangement = Arrangement.spacedBy(7.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(Modifier.size(7.dp).clip(RoundedCornerShape(100.dp)).background(color))
        Text(
            text = text.uppercase(),
            color = color,
            style = MaterialTheme.typography.labelLarge,
            fontSize = 10.sp,
            maxLines = 1,
        )
    }
}

@Composable
internal fun SectionHeading(
    eyebrow: String,
    title: String,
    modifier: Modifier = Modifier,
    trailing: (@Composable () -> Unit)? = null,
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.Bottom,
    ) {
        Column(Modifier.weight(1f)) {
            Text(
                eyebrow.uppercase(),
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                fontSize = 10.sp,
            )
            Spacer(Modifier.height(4.dp))
            Text(
                title,
                style = MaterialTheme.typography.headlineSmall,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
        }
        trailing?.invoke()
    }
}

@Composable
internal fun MetricTile(
    value: String,
    label: String,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(14.dp))
            .background(MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.72f))
            .padding(horizontal = 13.dp, vertical = 11.dp),
    ) {
        Text(value, fontWeight = FontWeight.Bold, fontSize = 20.sp)
        Text(label, color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 11.sp)
    }
}

@Composable
internal fun EmptyState(
    title: String,
    message: String,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 28.dp, vertical = 38.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Box(
            Modifier
                .size(42.dp)
                .clip(RoundedCornerShape(14.dp))
                .background(MaterialTheme.colorScheme.primary.copy(alpha = 0.10f)),
            contentAlignment = Alignment.Center,
        ) {
            Text("· · ·", color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Black)
        }
        Spacer(Modifier.height(14.dp))
        Text(title, style = MaterialTheme.typography.titleMedium)
        Spacer(Modifier.height(6.dp))
        Text(
            message,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            style = MaterialTheme.typography.bodyMedium,
            textAlign = androidx.compose.ui.text.style.TextAlign.Center,
        )
    }
}

internal fun formatElapsed(seconds: Long): String = "%02d:%02d".format(seconds / 60, seconds % 60)

internal fun formatClock(epochMs: Long): String = CLOCK_FORMAT.format(Instant.ofEpochMilli(epochMs))

internal fun compactBytes(bytes: Long): String = when {
    bytes >= 1_073_741_824L -> "%.1f GB".format(bytes / 1_073_741_824f)
    bytes >= 1_048_576L -> "%.1f MB".format(bytes / 1_048_576f)
    bytes >= 1_024L -> "%.1f KB".format(bytes / 1_024f)
    else -> "$bytes B"
}

private val CLOCK_FORMAT = DateTimeFormatter.ofPattern("HH:mm")
    .withZone(ZoneId.systemDefault())
