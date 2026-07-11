package com.offlineneuralfacilitator.onf

import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.offlineneuralfacilitator.onf.ai.FoundryCompanionDetector
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class FoundryCompanionDetectorTest {
    @Test
    fun detectsOfficialFoundryLocalAndroidCompanionWhenInstalled() {
        val context = ApplicationProvider.getApplicationContext<android.content.Context>()
        val status = FoundryCompanionDetector.inspect(context)
        assumeTrue("Official Foundry Local Android companion is not installed.", status.installed)
        assertTrue(status.versionName?.isNotBlank() == true)
        assertTrue((status.versionCode ?: 0) > 0)
    }
}
