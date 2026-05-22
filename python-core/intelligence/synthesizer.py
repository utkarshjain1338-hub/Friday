import logging
import random

logger = logging.getLogger("Friday-Synthesizer")

class ProceduralSynthesizer:
    def __init__(self):
        # Contextual templates based on predicted workflow
        self.templates = {
            "coding_mode": [
                "Preparing the development workspace.",
                "Initializing coding mode.",
                "Setting up your development environment."
            ],
            "focus_mode": [
                "Entering focus mode. Silencing distractions.",
                "Starting focus session.",
                "Optimizing workspace for concentration."
            ],
            "media_pause": [
                "Pausing playback.",
                "Stopping media.",
                "Muting audio."
            ],
            "media_play": [
                "Resuming playback.",
                "Starting media.",
                "Playing."
            ],
            "browser_search": [
                "Looking that up for you.",
                "Searching the web.",
                "Finding information."
            ]
        }
        
        self.generic_templates = [
            "Executing workflow {workflow}.",
            "Starting {workflow}.",
            "I'll handle {workflow}."
        ]

    def synthesize(self, predicted_workflow: str, context: dict = None) -> str:
        """Deterministically generates a response string for an action."""
        # Find exact matches in templates
        if predicted_workflow in self.templates:
            return random.choice(self.templates[predicted_workflow])
            
        # Fallback to generic template substitution
        template = random.choice(self.generic_templates)
        return template.replace("{workflow}", predicted_workflow.replace("_", " "))
