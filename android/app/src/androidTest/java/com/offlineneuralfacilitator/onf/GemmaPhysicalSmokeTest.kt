package com.offlineneuralfacilitator.onf

import android.os.SystemClock
import android.os.Build
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.offlineneuralfacilitator.onf.ai.EnginePhase
import com.offlineneuralfacilitator.onf.ai.LiteRtGemmaEngine
import kotlinx.coroutines.runBlocking
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File

@RunWith(AndroidJUnit4::class)
class GemmaPhysicalSmokeTest {
    @Test
    fun loadsPrivateGemmaAndGeneratesLocally() = runBlocking {
        val context = ApplicationProvider.getApplicationContext<android.content.Context>()
        assumeTrue("This multi-gigabyte readiness probe is restricted to the Fold7.", Build.DEVICE == "q7q")
        val model = File(context.filesDir, "models/gemma-4-E2B-it.litertlm")
        assumeTrue("Provision the physical Gemma model before this test.", model.isFile)

        val engine = LiteRtGemmaEngine(context)
        try {
            val loadStarted = SystemClock.elapsedRealtime()
            engine.load(model.absolutePath, model.name)
            val loadMs = SystemClock.elapsedRealtime() - loadStarted
            assertEquals(EnginePhase.READY, engine.status.value.phase)

            val generationStarted = SystemClock.elapsedRealtime()
            val response = engine.generate(
                systemInstruction = "You are a local device readiness probe. Be concise.",
                prompt = "Reply with a short sentence containing the exact token ONF-FOLD7-READY.",
            )
            val generationMs = SystemClock.elapsedRealtime() - generationStarted
            assertTrue(response.isNotBlank())
            assertTrue("Unexpected response: $response", response.contains("ONF-FOLD7-READY", ignoreCase = true))

            File(context.filesDir, "gemma_physical_benchmark.json").writeText(
                JSONObject().apply {
                    put("model", model.name)
                    put("backend", engine.status.value.backend)
                    put("load_ms", loadMs)
                    put("generation_ms", generationMs)
                    put("response", response)
                }.toString(2),
            )
        } finally {
            engine.close()
        }
    }
}
