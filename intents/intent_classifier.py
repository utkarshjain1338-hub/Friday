from typing import Tuple, Optional
from semantic.similarity_matcher import SimilarityMatcher


class IntentClassifier:
    """Classifies commands into high-level intent categories."""

    DEFAULT_CATEGORY = "general"

    CATEGORY_PATTERNS = {
        "browser_control": [
            "open website", "search google", "open youtube", "search youtube", "browser", "tab", "fullscreen",
        ],
        "media_control": [
            "play music", "pause music", "next song", "skip song", "volume up", "volume down", "mute", "unmute",
        ],
        "coding_workflow": [
            "open vscode", "open code", "coding mode", "launch terminal", "open terminal", "restore browser tabs",
        ],
        "messaging": [
            "send message", "reply", "open whatsapp", "message", "chat",
        ],
        "system_command": [
            "shutdown", "reboot", "lock screen", "suspend", "status", "battery", "cpu", "memory",
        ],
        "automation_request": [
            "workflow", "routine", "automate", "focus mode", "morning setup", "good morning", "start my day",
        ],
    }

    WORKFLOW_TRIGGERS = {
        "coding_mode": ["coding mode", "open vscode", "launch terminal", "code review ritual"],
        "focus_mode": ["focus mode", "this music is distracting", "enable dnd", "do not disturb"],
        "morning_setup": ["morning setup", "start my day", "good morning"],
    }

    def __init__(self):
        self.semantic_matcher = SimilarityMatcher(threshold=0.5)

    def classify(self, text: str) -> Tuple[str, str, float]:
        """Return (intent, category, confidence)."""
        normalized = text.lower().strip()
        if not normalized:
            return "unknown", self.DEFAULT_CATEGORY, 0.0

        # Exact phrase categories
        for category, patterns in self.CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if pattern in normalized:
                    return pattern.replace(" ", "_"), category, 0.9

        # Workflow triggers
        for workflow, patterns in self.WORKFLOW_TRIGGERS.items():
            for pattern in patterns:
                if pattern in normalized:
                    return workflow, "automation_request", 0.95

        # Try semantic similarity on the workflow triggers
        intent, score = self.semantic_matcher.match_intent(text)
        if intent and score >= 0.4:
            category = self._map_intent_to_category(intent)
            return intent, category, score

        # Fallback classification
        if any(term in normalized for term in ["open", "launch", "search", "play", "pause", "send", "delete", "move"]):
            return "action", "automation_request", 0.45

        return "unknown", self.DEFAULT_CATEGORY, 0.0

    @staticmethod
    def _map_intent_to_category(intent: str) -> str:
        if intent in ["toggle_mute", "volume_up", "volume_down", "media_play_pause", "media_next", "media_previous"]:
            return "media_control"
        if intent in ["close_active_window", "lock_screen", "system_suspend", "system_reboot", "system_shutdown"]:
            return "system_command"
        if intent in ["next_workspace", "prev_workspace", "toggle_fullscreen", "toggle_floating", "toggle_mic_mute", "brightness_up", "brightness_down"]:
            return "system_command"
        return "general"
