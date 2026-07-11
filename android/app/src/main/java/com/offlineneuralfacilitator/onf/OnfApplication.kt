package com.offlineneuralfacilitator.onf

import android.app.Application
import com.offlineneuralfacilitator.onf.ai.LiteRtGemmaEngine
import com.offlineneuralfacilitator.onf.ai.ModelManager
import com.offlineneuralfacilitator.onf.data.OnfRepository
import com.offlineneuralfacilitator.onf.domain.Facilitator
import com.offlineneuralfacilitator.onf.skills.SkillEngine

class OnfApplication : Application() {
    internal lateinit var container: OnfContainer
        private set

    override fun onCreate() {
        super.onCreate()
        container = OnfContainer(this)
    }
}

internal class OnfContainer(application: Application) {
    val repository = OnfRepository(application)
    val modelManager = ModelManager(application)
    val llm = LiteRtGemmaEngine(application)
    val skills = SkillEngine(application.assets)
    val facilitator = Facilitator(repository, skills, llm)
}
