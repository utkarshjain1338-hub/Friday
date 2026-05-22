from collections import Counter
from typing import Dict, Optional


class AdaptiveLearner:
    """Tracks command usage and builds simple routine suggestions."""

    def __init__(self, repeat_threshold: int = 3):
        self.command_counts = Counter()
        self.repeat_threshold = repeat_threshold
        self.known_routines: Dict[str, int] = {}

    def track_command(self, command: str) -> None:
        normalized = command.lower().strip()
        self.command_counts[normalized] += 1

    def suggest_routine(self) -> Optional[str]:
        for command, count in self.command_counts.most_common():
            if count >= self.repeat_threshold and command not in self.known_routines:
                self.known_routines[command] = count
                return f"I noticed you said '{command}' {count} times. Would you like me to create a routine for it?"
        return None

    def register_routine(self, routine_name: str) -> None:
        self.known_routines[routine_name.lower()] = self.command_counts.get(routine_name.lower(), 0)
