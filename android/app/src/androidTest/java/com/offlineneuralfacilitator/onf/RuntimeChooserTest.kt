package com.offlineneuralfacilitator.onf

import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.v2.createComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import com.offlineneuralfacilitator.onf.ai.EnginePhase
import com.offlineneuralfacilitator.onf.ai.FoundryCompanionStatus
import com.offlineneuralfacilitator.onf.ai.GalleryStatus
import com.offlineneuralfacilitator.onf.ai.LlmStatus
import com.offlineneuralfacilitator.onf.ai.ModelDescriptor
import com.offlineneuralfacilitator.onf.ui.MainUiState
import com.offlineneuralfacilitator.onf.ui.SystemSheet
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test

class RuntimeChooserTest {
    @get:Rule
    val composeRule = createComposeRule()

    @Test
    fun displaysRetainedGemmaModelsAndFoundrySdkBoundary() {
        val e2b = ModelDescriptor("gemma-4-E2B-it.litertlm", "/private/e2b", 2_588_147_712)
        val e4b = ModelDescriptor("gemma-4-E4B-it.litertlm", "/private/e4b", 3_659_530_240)
        var selectedPath: String? = null

        composeRule.setContent {
            MaterialTheme {
                SystemSheet(
                    uiState = MainUiState(
                        initialized = true,
                        llm = LlmStatus(
                            phase = EnginePhase.READY,
                            modelName = e2b.name,
                            backend = "CPU",
                            message = "Gemma is ready. Inference remains on this device.",
                        ),
                        foundryCompanion = FoundryCompanionStatus(
                            installed = true,
                            versionName = "0.1.5",
                            versionCode = 1050,
                        ),
                        gallery = GalleryStatus(installed = true, versionName = "0.1.1"),
                        deviceModels = listOf(e2b, e4b),
                        selectedModelPath = e2b.path,
                    ),
                    onDismiss = {},
                    onImportModel = {},
                    onImportKnowledge = {},
                    onSelectModel = { selectedPath = it },
                    onRemoveModel = {},
                    onOpenFoundryCompanion = {},
                    onRequestFoundrySdk = {},
                )
            }
        }

        composeRule.onNodeWithText("Microsoft Foundry Local").assertIsDisplayed()
        composeRule.onNodeWithText("REQUEST SDK ACCESS").assertIsDisplayed()
        composeRule.onAllNodesWithText(e2b.name).assertCountEquals(2)
        composeRule.onNodeWithText(e4b.name).assertExists()
        composeRule.onNodeWithText("ACTIVE").assertExists()
        composeRule.onNodeWithText("LOAD").performScrollTo().performClick()
        composeRule.runOnIdle { assertEquals(e4b.path, selectedPath) }
    }
}
