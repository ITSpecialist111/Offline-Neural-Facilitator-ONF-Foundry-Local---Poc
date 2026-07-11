package com.offlineneuralfacilitator.onf

import android.os.SystemClock
import android.os.Build
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.offlineneuralfacilitator.onf.ai.EnginePhase
import com.offlineneuralfacilitator.onf.ai.LiteRtGemmaEngine
import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File

@RunWith(AndroidJUnit4::class)
class GemmaModelSwitchPhysicalTest {
    @Test
    fun switchesE2bToE4bAndBackWithoutRestarting() = runBlocking {
        val context = ApplicationProvider.getApplicationContext<android.content.Context>()
        assumeTrue("This multi-gigabyte switching probe is restricted to the Fold7.", Build.DEVICE == "q7q")
        val e2b = File(context.filesDir, "models/gemma-4-E2B-it.litertlm")
        val e4b = File(context.filesDir, "models/gemma-4-E4B-it.litertlm")
        assumeTrue("Provision both physical Gemma models before this test.", e2b.isFile && e4b.isFile)

        val engine = LiteRtGemmaEngine(context)
        val results = JSONArray()
        try {
            listOf(
                e2b to "ONF-E2B-READY",
                e4b to "ONF-E4B-READY",
                e2b to "ONF-E2B-RETURNED",
            ).forEach { (model, token) ->
                val loadStarted = SystemClock.elapsedRealtime()
                engine.load(model.absolutePath, model.name)
                val loadMs = SystemClock.elapsedRealtime() - loadStarted
                assertEquals(EnginePhase.READY, engine.status.value.phase)
                assertEquals(model.name, engine.status.value.modelName)

                val generationStarted = SystemClock.elapsedRealtime()
                val response = engine.generate(
                    systemInstruction = "You are a local device readiness probe. Follow the requested output exactly.",
                    prompt = "Reply with the exact token $token and no other text.",
                )
                val generationMs = SystemClock.elapsedRealtime() - generationStarted
                assertTrue("Unexpected response from ${model.name}: $response", response.contains(token, ignoreCase = true))

                results.put(
                    JSONObject().apply {
                        put("model", model.name)
                        put("size_bytes", model.length())
                        put("backend", engine.status.value.backend)
                        put("load_ms", loadMs)
                        put("generation_ms", generationMs)
                        put("response", response)
                    },
                )
            }

            File(context.filesDir, "gemma_model_switch_benchmark.json").writeText(
                JSONObject().apply {
                    put("sequence", results)
                }.toString(2),
            )
        } finally {
            engine.close()
        }
    }
}
