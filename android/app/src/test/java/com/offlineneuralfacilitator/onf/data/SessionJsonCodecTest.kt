package com.offlineneuralfacilitator.onf.data

import com.offlineneuralfacilitator.onf.domain.model.ActionItem
import com.offlineneuralfacilitator.onf.domain.model.Decision
import com.offlineneuralfacilitator.onf.domain.model.Insight
import com.offlineneuralfacilitator.onf.domain.model.InsightKind
import com.offlineneuralfacilitator.onf.domain.model.OnfState
import com.offlineneuralfacilitator.onf.domain.model.SessionInfo
import com.offlineneuralfacilitator.onf.domain.model.TranscriptMessage
import org.junit.Assert.assertEquals
import org.junit.Test

class SessionJsonCodecTest {
    @Test
    fun `round trips the canonical meeting record`() {
        val state = OnfState(
            session = SessionInfo.create("Recovery decision"),
            transcript = listOf(TranscriptMessage(role = "participant", speaker = "Priya", content = "We need a clean restore.")),
            insights = listOf(Insight(kind = InsightKind.KNOWLEDGE, title = "Evidence", text = "Backup is nine hours old.", citation = "Recovery Card")),
            decisions = listOf(Decision(text = "Begin clean restore")),
            actions = listOf(ActionItem(text = "Verify backup", owner = "Marcus", due = "Now")),
            activeSkills = setOf("crisis-manager"),
        )
        val recovered = SessionJsonCodec.decode(SessionJsonCodec.encode(state))
        assertEquals(state.session.topic, recovered.session.topic)
        assertEquals("Priya", recovered.transcript.single().speaker)
        assertEquals("Recovery Card", recovered.insights.single().citation)
        assertEquals("Marcus", recovered.actions.single().owner)
        assertEquals(setOf("crisis-manager"), recovered.activeSkills)
    }
}
