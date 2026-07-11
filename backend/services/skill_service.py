import os
import yaml

class SkillService:
    def __init__(self, skills_dir="skills"):
        self.skills_dir = skills_dir
        self.loaded_skills = {}
        self.load_skills()

    def load_skills(self):
        """Scans the skills directory for SKILL.md files."""
        self.loaded_skills.clear()
        if not os.path.exists(self.skills_dir):
            os.makedirs(self.skills_dir)
            return

        print(f"Scanning skills in '{self.skills_dir}'...")
        for root, dirs, files in os.walk(self.skills_dir):
            for file in files:
                if file.lower().endswith(".md"):
                    self._parse_skill(os.path.join(root, file))

    def _parse_skill(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    yaml_content = parts[1]
                    instructions = parts[2].strip()
                    
                    metadata = yaml.safe_load(yaml_content)
                    if metadata:
                        skill_name = metadata.get('name', 'unknown')
                        self.loaded_skills[skill_name] = {
                            "metadata": metadata,
                            "instructions": instructions,
                            "triggers": [t.lower() for t in metadata.get("triggers", [])]
                        }
                        print(f"Loaded Skill: {skill_name}")
        except Exception as e:
            print(f"Error loading skill {filepath}: {e}")

    def list_skills(self):
        return list(self.loaded_skills.keys())

    def get_system_prompt_addition(self):
        """Returns minimal list effectively, or full instructions if we want static loading."""
        return "" # We are moving to dynamic loading

    def check_triggers(self, text):
        """Returns tuple (instructions_str, triggered_skills_list)."""
        triggered_instructions = ""
        triggered_skills = []
        text = text.lower()
        
        for name, data in self.loaded_skills.items():
            for trigger in data.get("triggers", []):
                if trigger in text:
                    triggered_instructions += f"\n\n[System: Activate Skill '{name}']\n{data['instructions']}\n"
                    triggered_skills.append(name)
                    break # Trigger once per skill
        
        return triggered_instructions, triggered_skills
