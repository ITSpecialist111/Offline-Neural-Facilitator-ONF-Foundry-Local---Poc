package com.offlineneuralfacilitator.onf.skills

import android.content.res.AssetManager

internal data class FacilitatorSkill(
    val name: String,
    val triggers: List<String>,
    val instructions: String,
)

internal data class SkillMatch(
    val names: List<String>,
    val instructions: String,
)

internal class SkillEngine(
    private val assets: AssetManager,
) {
    private val skills: List<FacilitatorSkill> by lazy(::loadSkills)

    fun list(): List<String> = skills.map(FacilitatorSkill::name)

    fun match(text: String): SkillMatch {
        val lower = text.lowercase()
        val matches = skills.filter { skill -> skill.triggers.any(lower::contains) }
        return SkillMatch(
            names = matches.map(FacilitatorSkill::name),
            instructions = matches.joinToString("\n\n") { skill ->
                "[Activate specialist skill: ${skill.name}]\n${skill.instructions}"
            },
        )
    }

    private fun loadSkills(): List<FacilitatorSkill> = assets.list(SKILLS_ROOT)
        .orEmpty()
        .filter { it.endsWith(".md", ignoreCase = true) }
        .mapNotNull { filename ->
            assets.open("$SKILLS_ROOT/$filename").bufferedReader().use { parse(it.readText(), filename) }
        }

    internal fun parse(content: String, fallbackName: String): FacilitatorSkill? {
        if (!content.startsWith("---")) return null
        val parts = content.split("---", limit = 3)
        if (parts.size < 3) return null
        val frontmatter = parts[1]
        val name = Regex("(?m)^name:\\s*[\"']?(.+?)[\"']?\\s*$")
            .find(frontmatter)
            ?.groupValues
            ?.getOrNull(1)
            ?.trim()
            ?: fallbackName.removeSuffix(".md")
        val inlineTriggers = Regex("(?m)^triggers:\\s*\\[(.*)]\\s*$")
            .find(frontmatter)
            ?.groupValues
            ?.getOrNull(1)
            ?.split(',')
            ?.map { it.trim(' ', '\'', '"').lowercase() }
            .orEmpty()
        val frontmatterLines = frontmatter.lines()
        val triggerLine = frontmatterLines.indexOfFirst { it.trimStart().startsWith("triggers:") }
        val triggerListBlock = if (triggerLine >= 0) {
            frontmatterLines.drop(triggerLine + 1)
                .takeWhile { line -> line.isBlank() || line.firstOrNull()?.isWhitespace() == true }
                .joinToString("\n")
        } else {
            ""
        }
        val listTriggers = Regex("(?m)^\\s*-\\s*[\"']?(.+?)[\"']?\\s*$")
            .findAll(triggerListBlock)
            .map { it.groupValues[1].trim().lowercase() }
            .toList()
        val triggers = (inlineTriggers + listTriggers).filter(String::isNotBlank).distinct()
        return FacilitatorSkill(name, triggers, parts[2].trim()).takeIf { it.triggers.isNotEmpty() }
    }

    companion object {
        private const val SKILLS_ROOT = "skills"
    }
}
