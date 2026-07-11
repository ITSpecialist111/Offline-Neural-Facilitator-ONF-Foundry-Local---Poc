package com.offlineneuralfacilitator.onf

import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.offlineneuralfacilitator.onf.skills.SkillEngine
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class SkillEngineTest {
    private val context = ApplicationProvider.getApplicationContext<android.content.Context>()

    @Test
    fun loadsBundledSkillsAndMatchesRansomware() {
        val engine = SkillEngine(context.assets)
        assertEquals(5, engine.list().size)
        val match = engine.match("The hospital ransomware incident threatens patient safety")
        assertTrue("ransomware-incident-response" in match.names)
        assertTrue("crisis-manager" in match.names)
    }

    @Test
    fun multilineTriggerParsingStopsAtNextTopLevelKey() {
        val engine = SkillEngine(context.assets)
        val skill = engine.parse(
            """
                ---
                name: sample
                triggers:
                  - alpha
                  - beta
                description: must-not-be-a-trigger
                ---
                Instructions
            """.trimIndent(),
            "sample.md",
        )
        assertEquals(listOf("alpha", "beta"), skill?.triggers)
    }
}
