package com.offlineneuralfacilitator.onf

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.isDisplayed
import androidx.compose.ui.test.junit4.v2.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import org.junit.Rule
import org.junit.Test

class MainActivityTest {
    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun opensPrivateWorkspaceWithoutNetworkSetup() {
        composeRule.waitUntil(timeoutMillis = 10_000) {
            composeRule.onAllNodes(androidx.compose.ui.test.hasText("OFFLINE NEURAL FACILITATOR"))
                .fetchSemanticsNodes().isNotEmpty()
        }
        composeRule.onNodeWithText("OFFLINE NEURAL FACILITATOR").assertIsDisplayed()
        composeRule.onNodeWithText("START PRIVATE CAPTURE").assertIsDisplayed()
    }

    @Test
    fun showcaseBuildsCanonicalDecisionState() {
        composeRule.waitUntil(timeoutMillis = 10_000) {
            composeRule.onAllNodes(androidx.compose.ui.test.hasText("SHOWCASE"))
                .fetchSemanticsNodes().isNotEmpty()
        }
        composeRule.onNodeWithText("SHOWCASE").performClick()
        composeRule.waitUntil(timeoutMillis = 10_000) {
            composeRule.onAllNodes(androidx.compose.ui.test.hasText("Code Blue: Ransomware at Northstar Hospital"))
                .fetchSemanticsNodes().isNotEmpty()
        }
        composeRule.waitUntil(timeoutMillis = 10_000) {
            runCatching { composeRule.onNodeWithText("Decision frame clarified").isDisplayed() }
                .getOrDefault(false)
        }
        composeRule.onNodeWithText("Decision frame clarified")
            .assertIsDisplayed()
    }
}
