import json
import os
import logging

logger = logging.getLogger("Friday-SemanticMemory")

class SemanticMemory:
    def __init__(self, memory_file="semantic_memory.json"):
        self.memory_file = memory_file
        self.learned_phrases = self._load()

    def _load(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load semantic memory: {e}")
        return {}

    def _save(self):
        try:
            with open(self.memory_file, "w") as f:
                json.dump(self.learned_phrases, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save semantic memory: {e}")

    def learn_phrase(self, phrase: str, intent: str):
        if intent not in self.learned_phrases:
            self.learned_phrases[intent] = []
        if phrase not in self.learned_phrases[intent]:
            self.learned_phrases[intent].append(phrase)
            self._save()
            logger.info(f"Learned new phrase for {intent}: '{phrase}'")

    def get_learned_phrases(self):
        return self.learned_phrases
