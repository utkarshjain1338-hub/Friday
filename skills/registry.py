from typing import Dict, List, Optional
from .base_skill import BaseSkill


class SkillRegistry:
    def __init__(self):
        self._skills: Dict[str, BaseSkill] = {}

    def register(self, skill: BaseSkill):
        self._skills[skill.name] = skill

    def get(self, name: str) -> Optional[BaseSkill]:
        return self._skills.get(name)

    def find_for_command(self, phrase: str) -> List[BaseSkill]:
        phrase = phrase.lower()
        matches = []
        for skill in self._skills.values():
            for cmd in getattr(skill, "commands", []):
                if cmd in phrase:
                    matches.append(skill)
                    break
        return matches

    def all_skills(self):
        return list(self._skills.values())
