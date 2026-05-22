import logging

logger = logging.getLogger("Friday-ContextMapper")

class ContextualMeaningMapper:
    def __init__(self):
        # We simulate system state context for now.
        # This would be updated via the System State Engine.
        self.system_state = {
            "active_app": "Firefox",
            "media_playing": True,
            "browser_tab": "YouTube",
            "workspace": 1
        }

    def update_state(self, key: str, value: any):
        self.system_state[key] = value

    def contextualize(self, utterance: str, matched_intent: dict) -> dict:
        intent = matched_intent.get("intent")
        
        # Example of contextual override:
        if "pause this" in utterance.lower() or intent == "media_pause":
            if self.system_state.get("media_playing") and self.system_state.get("active_app") == "Firefox":
                logger.info("Contextual Match: Pausing Firefox media instead of global Spotify.")
                matched_intent["contextualized_action"] = "pause_firefox_media"
            else:
                matched_intent["contextualized_action"] = "pause_global_media"
                
        # If the intent is ambiguous but context makes it clear:
        if intent == "unknown" and "this" in utterance.lower():
            if self.system_state.get("active_app") == "VSCode":
                logger.info("Context inferred: User is referring to VSCode.")
                matched_intent["contextualized_action"] = "inspect_vscode"
                
        return matched_intent
