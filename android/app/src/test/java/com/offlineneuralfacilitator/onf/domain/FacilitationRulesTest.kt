package com.offlineneuralfacilitator.onf.domain

import com.offlineneuralfacilitator.onf.domain.model.TranscriptMessage
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class FacilitationRulesTest {
    @Test
    fun `normalizes the Code Blue title`() {
        val title = FacilitationRules.explicitTitle(
            "Today's meeting is about Code Blue ransomware at North Star Hospital.",
        )
        assertEquals("Code Blue: Ransomware at Northstar Hospital", title)
    }

    @Test
    fun `extracts owner due time and action text`() {
        val actions = FacilitationRules.actions(
            "Action item: Marcus will verify backup integrity and start the Tier One restore within thirty minutes.",
        )
        assertEquals(1, actions.size)
        assertEquals("Marcus", actions.single().owner)
        assertEquals("Within thirty minutes", actions.single().due)
        assertEquals("Verify backup integrity and start the Tier One restore", actions.single().text)
    }

    @Test
    fun `extracts an explicit decision`() {
        assertEquals(
            "Begin the verified clean restore",
            FacilitationRules.decision("We have decided to begin the verified clean restore."),
        )
    }

    @Test
    fun `detects a recent alignment gap`() {
        val messages = listOf(
            TranscriptMessage(role = "participant", speaker = "A", content = "I disagree; that is too risky."),
            TranscriptMessage(role = "participant", speaker = "B", content = "I am not convinced the shortcut will work."),
        )
        assertTrue(FacilitationRules.hasAlignmentGap(messages))
    }
}
