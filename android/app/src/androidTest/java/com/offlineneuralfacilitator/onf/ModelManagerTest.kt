package com.offlineneuralfacilitator.onf

import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.offlineneuralfacilitator.onf.ai.ModelDescriptor
import com.offlineneuralfacilitator.onf.ai.ModelManager
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.util.UUID

@RunWith(AndroidJUnit4::class)
class ModelManagerTest {
    @Test
    fun selectingAnotherModelRetainsBothUntilExplicitRemoval() {
        val context = ApplicationProvider.getApplicationContext<android.content.Context>()
        val suffix = UUID.randomUUID().toString()
        val directory = File(context.cacheDir, "model-registry-$suffix").apply(File::mkdirs)
        val preferences = "model-registry-$suffix"
        val manager = ModelManager(context, preferences, directory)
        val e2bFile = File(directory, "gemma-4-E2B-it.litertlm").apply { writeBytes(byteArrayOf(2)) }
        val e4bFile = File(directory, "gemma-4-E4B-it.litertlm").apply { writeBytes(byteArrayOf(4)) }
        val e2b = ModelDescriptor(e2bFile.name, e2bFile.absolutePath, e2bFile.length())
        val e4b = ModelDescriptor(e4bFile.name, e4bFile.absolutePath, e4bFile.length())

        try {
            manager.select(e2b)
            manager.select(e4b)

            assertEquals(e4b.path, manager.selected()?.path)
            assertEquals(setOf(e2b.path, e4b.path), manager.available().map { it.path }.toSet())
            assertTrue(e2bFile.isFile)
            assertTrue(e4bFile.isFile)
            assertTrue(manager.remove(e2b))
            assertFalse(e2bFile.exists())
            assertFalse(manager.remove(e4b))
            assertTrue(e4bFile.isFile)
        } finally {
            context.getSharedPreferences(preferences, android.content.Context.MODE_PRIVATE).edit().clear().commit()
            directory.deleteRecursively()
        }
    }
}