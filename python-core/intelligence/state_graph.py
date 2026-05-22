import logging

logger = logging.getLogger("Friday-StateGraph")

class StateGraph:
    def __init__(self):
        # Graph nodes mapping apps to their contextual category
        self.app_categories = {
            "code": "development",
            "alacritty": "development",
            "kitty": "development",
            "brave-browser": "browsing",
            "firefox": "browsing",
            "spotify": "media",
            "discord": "communication",
            "steam": "gaming"
        }
        
        # Current active state nodes
        self.current_state = {
            "active_app": None,
            "active_category": None,
            "browser_url": None,
            "is_media_playing": False
        }

    def update_node(self, key: str, value: any):
        self.current_state[key] = value
        
        if key == "active_app":
            cat = self.app_categories.get(value.lower(), "unknown")
            self.current_state["active_category"] = cat
            logger.debug(f"StateGraph: App '{value}' classified as '{cat}'")

    def get_current_category(self) -> str:
        return self.current_state.get("active_category", "unknown")
