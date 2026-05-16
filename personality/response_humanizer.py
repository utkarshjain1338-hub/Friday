"""
Personality and Speech Humanization System
Transforms robotic responses into natural, human-like speech
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum
import random
from loguru import logger


class EmotionalState(str, Enum):
    """Emotional states for response styling"""
    HAPPY = "happy"
    HELPFUL = "helpful"
    CURIOUS = "curious"
    CONFIDENT = "confident"
    UNCERTAIN = "uncertain"
    TIRED = "tired"
    EXCITED = "excited"
    CALM = "calm"


class SpeechStyle(str, Enum):
    """Speech style options"""
    FORMAL = "formal"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"


class ResponseHumanizer:
    """
    Transforms robotic/technical responses into natural, human-like speech
    """
    
    def __init__(self):
        self.current_emotion = EmotionalState.HELPFUL
        self.speaking_style = SpeechStyle.FRIENDLY
        self.conversation_flow = []
    
    # ===== FILLER WORDS & TRANSITIONS =====
    
    FILLERS = {
        "happy": ["Oh great!", "Awesome!", "Wonderful!"],
        "helpful": ["Sure!", "Of course!", "Happy to help!"],
        "curious": ["Interesting!", "Let me check...", "Good question!"],
        "confident": ["Absolutely!", "No problem!", "I've got this!"],
        "uncertain": ["Hmm...", "Let me think...", "I'm not entirely sure..."],
        "tired": ["Sure...", "Okay...", "Got it..."],
        "excited": ["Yes! Yes!", "Oh! That's great!", "Amazing!"],
        "calm": ["Alright", "Let's see", "I understand"],
    }
    
    TRANSITIONS = {
        "then": ["Then", "After that", "Next", "Subsequently"],
        "because": ["because", "since", "as", "given that"],
        "however": ["However", "But", "Though", "On the other hand"],
        "emphasis": ["Definitely", "Absolutely", "Certainly", "Without a doubt"],
        "question": ["Do you think", "Would you", "Could you", "Want to"],
    }
    
    CONVERSATIONAL_STARTERS = [
        "So... ",
        "Well, ",
        "You know, ",
        "Interestingly, ",
        "By the way, ",
        "Actually, ",
        "Here's the thing: ",
    ]
    
    # ===== CORE HUMANIZATION =====
    
    def humanize_response(
        self,
        response: str,
        emotion: Optional[EmotionalState] = None,
        style: Optional[SpeechStyle] = None,
        add_pacing: bool = True
    ) -> str:
        """
        Transform a technical response into natural speech
        
        Args:
            response: Original response text
            emotion: Emotional state (uses current if None)
            style: Speaking style (uses current if None)
            add_pacing: Whether to add pacing markers
            
        Returns:
            Humanized response
        """
        if emotion:
            self.current_emotion = emotion
        if style:
            self.speaking_style = style
        
        # Apply transformations in order
        humanized = response
        
        # 1. Add conversational elements
        humanized = self._add_conversational_elements(humanized)
        
        # 2. Add appropriate filler words
        humanized = self._add_filler_words(humanized)
        
        # 3. Improve transitions
        humanized = self._improve_transitions(humanized)
        
        # 4. Add emotion styling
        humanized = self._apply_emotion_styling(humanized)
        
        # 5. Add pacing markers if requested
        if add_pacing:
            humanized = self._add_pacing_markers(humanized)
        
        # Track in conversation flow
        self.conversation_flow.append({
            "original": response,
            "humanized": humanized,
            "emotion": str(self.current_emotion),
            "style": str(self.speaking_style)
        })
        
        logger.info(f"Humanized response (emotion: {self.current_emotion})")
        return humanized
    
    def _add_conversational_elements(self, text: str) -> str:
        """Add conversational starters and connectors"""
        sentences = text.split('. ')
        
        # Add starter to first sentence if it's a statement
        if sentences and len(sentences[0]) > 10:
            if not any(text.startswith(w) for w in ["The", "You", "I", "It", "So", "Well", "Actually"]):
                sentences[0] = random.choice(self.CONVERSATIONAL_STARTERS) + sentences[0]
        
        return '. '.join(sentences)
    
    def _add_filler_words(self, text: str) -> str:
        """Add emotion-appropriate filler words"""
        emotion_key = self.current_emotion.value
        fillers = self.FILLERS.get(emotion_key, self.FILLERS["helpful"])
        
        # Don't add if already has natural opening
        if any(text.startswith(f) for f in fillers):
            return text
        
        # Add filler at appropriate point (before main content)
        sentences = text.split('. ')
        if sentences:
            # Pick random filler
            filler = random.choice(fillers)
            sentences[0] = f"{filler} {sentences[0]}"
        
        return '. '.join(sentences)
    
    def _improve_transitions(self, text: str) -> str:
        """Improve transitions between ideas"""
        # Replace "then" with varied transitions
        transitions = self.TRANSITIONS["then"]
        for i, transition in enumerate(transitions):
            if "then " in text.lower():
                text = text.replace("then ", f"{transitions[(i+1) % len(transitions)]} ", 1)
        
        # Handle "because" transitions
        if " because " in text:
            transitions = self.TRANSITIONS["because"]
            text = text.replace(" because ", f" {random.choice(transitions)} ", 1)
        
        return text
    
    def _apply_emotion_styling(self, text: str) -> str:
        """Apply emotion-specific styling"""
        emotion = self.current_emotion
        
        if emotion == EmotionalState.EXCITED:
            # Add exclamation marks
            if not text.endswith("!"):
                text = text.rstrip(".") + "!"
            text = text.replace(".", "!", 1)  # First sentence excited
        
        elif emotion == EmotionalState.TIRED:
            # Remove enthusiasm, keep calm
            text = text.replace("!", ".")
            text = text.replace("?!", "?")
        
        elif emotion == EmotionalState.UNCERTAIN:
            # Add hedging language
            if "definitely" in text:
                text = text.replace("definitely", "probably")
            text = text.replace(".", "...", 1)  # Thoughtful pause
        
        elif emotion == EmotionalState.CONFIDENT:
            # Add certainty markers
            text = text.replace("might", "will")
            text = text.replace("could", "can")
        
        return text
    
    def _add_pacing_markers(self, text: str) -> str:
        """Add pacing markers for natural speech timing"""
        # Add breathing pauses at sentence boundaries
        text = text.replace(". ", ".\n[pause:short] ")
        
        # Add longer pauses after commas in lists
        parts = text.split(", ")
        if len(parts) > 2:
            text = ", \n[pause:medium] ".join(parts)
        
        # Add thought markers
        if "..." in text:
            text = text.replace("...", "\n[pause:long]")
        
        return text
    
    # ===== EMOTION DETECTION =====
    
    def detect_emotion_from_context(self, context: Dict) -> EmotionalState:
        """Detect appropriate emotion from context"""
        # Analyze context to determine emotion
        if context.get("user_urgency") == "high":
            return EmotionalState.EXCITED
        
        if context.get("task_success", True):
            if context.get("complexity") == "high":
                return EmotionalState.CONFIDENT
            return EmotionalState.HAPPY
        
        if context.get("uncertainty_level", 0) > 0.7:
            return EmotionalState.UNCERTAIN
        
        if context.get("repetition_count", 0) > 3:
            return EmotionalState.TIRED
        
        return EmotionalState.HELPFUL
    
    # ===== RESPONSE TEMPLATES =====
    
    def get_opening(self, context: Optional[Dict] = None) -> str:
        """Get appropriate opening phrase"""
        emotion = EmotionalState.HELPFUL
        if context:
            emotion = self.detect_emotion_from_context(context)
        
        openings = {
            EmotionalState.HAPPY: ["Oh, great question!", "I love helping with this!"],
            EmotionalState.EXCITED: ["Yes! Let's do this!", "I'm so ready for this!"],
            EmotionalState.CONFIDENT: ["I know exactly what to do.", "This is straightforward."],
            EmotionalState.HELPFUL: ["Sure, I can help!", "Let me take care of that."],
            EmotionalState.CALM: ["Alright, let's approach this carefully.", "Let me think about this."],
        }
        
        return random.choice(openings.get(emotion, openings[EmotionalState.HELPFUL]))
    
    def get_closing(self, success: bool = True) -> str:
        """Get appropriate closing phrase"""
        if success:
            closings = [
                "There you go!",
                "All set!",
                "Hope that helps!",
                "Enjoy!",
                "Let me know if you need anything else!",
            ]
        else:
            closings = [
                "Sorry about that...",
                "I'm working on it...",
                "Let me try that again.",
                "Give me a moment...",
            ]
        
        return random.choice(closings)
    
    # ===== CONVERSATIONAL FLOW =====
    
    def get_conversation_summary(self) -> Dict:
        """Get summary of conversation tone"""
        if not self.conversation_flow:
            return {"messages": 0}
        
        emotions = [msg.get("emotion") for msg in self.conversation_flow]
        styles = [msg.get("style") for msg in self.conversation_flow]
        
        return {
            "messages": len(self.conversation_flow),
            "dominant_emotion": max(set(emotions), key=emotions.count),
            "dominant_style": max(set(styles), key=styles.count),
            "variety": len(set(emotions)),
        }
    
    def reset_conversation(self):
        """Reset conversation tracking"""
        self.conversation_flow = []
        self.current_emotion = EmotionalState.HELPFUL
        self.speaking_style = SpeechStyle.FRIENDLY


class PacingController:
    """
    Controls speaking pacing and rhythm
    """
    
    def __init__(self, default_speed: str = "normal"):
        """
        Initialize pacing controller
        
        Args:
            default_speed: normal, slow, fast
        """
        self.default_speed = default_speed
        self.current_speed = default_speed
    
    # Pause durations in milliseconds
    PAUSE_DURATIONS = {
        "short": 200,      # Quick pause
        "medium": 500,     # Normal pause
        "long": 1000,      # Thought pause
        "emphasis": 300,   # Emphasis pause
    }
    
    SPEED_FACTORS = {
        "slow": 1.5,
        "normal": 1.0,
        "fast": 0.6,
    }
    
    def add_pacing_to_text(self, text: str) -> str:
        """Add pacing markers to text"""
        # Insert pacing markers at natural break points
        text = text.replace(".", ".\n[pause:medium]")
        text = text.replace("!", "!\n[pause:short]")
        text = text.replace("?", "?\n[pause:medium]")
        
        # Handle commas
        text = text.replace(", ", ",\n[pause:short] ")
        
        return text
    
    def get_pause_duration(self, pause_type: str, speed: Optional[str] = None) -> int:
        """Get pause duration in milliseconds"""
        if speed is None:
            speed = self.current_speed
        
        base_duration = self.PAUSE_DURATIONS.get(pause_type, 500)
        speed_factor = self.SPEED_FACTORS.get(speed, 1.0)
        
        return int(base_duration * speed_factor)
    
    def set_speed(self, speed: str):
        """Set speaking speed"""
        if speed in self.SPEED_FACTORS:
            self.current_speed = speed
        else:
            logger.warning(f"Unknown speed: {speed}, using default")
    
    def adjust_for_emotion(self, emotion: EmotionalState) -> str:
        """Adjust pacing based on emotion"""
        if emotion == EmotionalState.EXCITED:
            return "fast"
        elif emotion == EmotionalState.TIRED:
            return "slow"
        elif emotion == EmotionalState.UNCERTAIN:
            return "slow"
        else:
            return "normal"
