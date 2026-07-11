package com.offlineneuralfacilitator.onf

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.isDisplayed
import androidx.compose.ui.test.junit4.v2.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import org.junit.Before
import org.junit.Rule
import org.junit.Test

class MainActivityTest {
    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    @Before
    fun makeTestActivityVisibleWhileDeviceIsLocked() {
        composeRule.activityRule.scenario.onActivity { activity ->
            activity.setShowWhenLocked(true)
            activity.setTurnScreenOn(true)
        }
    }

    @Test
    fun opensPrivateWorkspaceWithoutNetworkSetup() {
        waitForText("OFFLINE NEURAL FACILITATOR")
        composeRule.onNodeWithText("OFFLINE NEURAL FACILITATOR").assertIsDisplayed()
        composeRule.onNodeWithText("START PRIVATE CAPTURE").assertIsDisplayed()
    }

    @Test
    fun showcaseBuildsCanonicalDecisionState() {
        waitForText("SHOWCASE")
        composeRule.waitUntil(timeoutMillis = 30_000) {
            runCatching {
                composeRule.onNodeWithText("SHOWCASE").assertIsEnabled()
                true
            }.getOrDefault(false)
        }
        composeRule.onNodeWithText("SHOWCASE").performClick()
        waitForText("Code Blue: Ransomware at Northstar Hospital")
        composeRule.waitUntil(timeoutMillis = 10_000) {
            runCatching { composeRule.onNodeWithText("Decision frame clarified").isDisplayed() }
                .getOrDefault(false)
        }
        composeRule.onNodeWithText("Decision frame clarified")
            .assertIsDisplayed()
    }

    private fun waitForText(text: String) {
        composeRule.waitUntil(timeoutMillis = 30_000) {
            runCatching {
                composeRule.onAllNodes(androidx.compose.ui.test.hasText(text))
                    .fetchSemanticsNodes().isNotEmpty()
            }.getOrDefault(false)
        }
    }
}
