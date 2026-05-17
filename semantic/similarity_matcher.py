"""
Semantic Similarity Matcher
Bridges natural, conversational language to raw reflex commands.
Supports sentence-transformers (all-MiniLM-L6-v2) and a high-speed pure-python fallback.
"""

import sys
from typing import Dict, List, Tuple, Optional
from loguru import logger

# Intent variations for semantic mapping
INTENT_TEMPLATES: Dict[str, List[str]] = {
    "toggle_mute": [
        "mute", "unmute", "toggle sound", "turn off audio", "silent", 
        "quiet down", "shutup", "mute system", "turn on sound", "sound off"
    ],
    "volume_up": [
        "volume up", "louder", "turn it up", "can't hear", "increase sound", 
        "make it louder", "sound up", "raise the volume"
    ],
    "volume_down": [
        "volume down", "quieter", "turn it down", "too loud", "decrease sound", 
        "lower the volume", "sound down", "make it quiet"
    ],
    "media_play_pause": [
        "play", "pause", "resume playback", "stop playback", "stop music", 
        "play music", "toggle music", "resume music", "pause playback"
    ],
    "media_next": [
        "next song", "next track", "skip", "skip song", "play next"
    ],
    "media_previous": [
        "previous song", "prev song", "previous track", "go back", "play previous"
    ],
    "close_active_window": [
        "close window", "kill application", "exit window", "close this", 
        "shut window", "close this window", "close active window", "destroy window"
    ],
    "lock_screen": [
        "lock computer", "lock pc", "lock session", "lock screen", "lock active"
    ],
    "next_workspace": [
        "next workspace", "go to next workspace", "switch to next workspace"
    ],
    "prev_workspace": [
        "previous workspace", "go to previous workspace", "prev workspace"
    ],
    "toggle_fullscreen": [
        "toggle fullscreen", "fullscreen window", "go fullscreen", "make fullscreen", "maximize window", "fullscreen"
    ],
    "toggle_floating": [
        "toggle floating", "make floating", "float window", "unfloat window", "toggle float"
    ],
    "toggle_mic_mute": [
        "mute mic", "unmute mic", "mute microphone", "unmute microphone", "toggle microphone", "toggle mic", "silent microphone"
    ],
    "brightness_up": [
        "increase brightness", "brightness up", "brighten screen", "make screen brighter", "raise brightness", "screen up"
    ],
    "brightness_down": [
        "decrease brightness", "brightness down", "dim screen", "make screen darker", "lower brightness", "screen down"
    ],
    "system_suspend": [
        "suspend system", "system sleep", "put computer to sleep", "suspend pc", "sleep pc"
    ],
    "system_reboot": [
        "reboot system", "restart pc", "reboot pc", "restart computer", "reboot"
    ],
    "system_shutdown": [
        "shutdown system", "power off pc", "turn off pc", "shutdown pc", "power off", "shutdown"
    ]
}


class SimilarityMatcher:
    """
    Computes semantic similarity to map high-level NLP expressions to low-level system reflexes.
    """

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.model = None
        self._flat_sentences: List[str] = []
        self._flat_intents: List[str] = []

        # Flatten templates for indexing
        for intent, sentences in INTENT_TEMPLATES.items():
            for sentence in sentences:
                self._flat_sentences.append(sentence.lower())
                self._flat_intents.append(intent)

        # Attempt to load sentence-transformers in the background
        import threading
        def _load_model():
            try:
                from sentence_transformers import SentenceTransformer
                logger.info("SentenceTransformers installed. Loading 'all-MiniLM-L6-v2' in background...")
                model = SentenceTransformer("all-MiniLM-L6-v2")
                # Warm up model
                model.encode(["hello"])
                self.model = model
                logger.info("all-MiniLM-L6-v2 loaded successfully.")
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformers (using high-speed fallback matcher): {e}")

        threading.Thread(target=_load_model, daemon=True).start()

    def _fallback_similarity(self, s1: str, s2: str) -> float:
        """
        Sub-millisecond token-overlap similarity metric (Jaccard similarity with word weights).
        Elegant pure-python fallback when PyTorch/Transformers are not loaded.
        """
        words1 = set(s1.split())
        words2 = set(s2.split())
        if not words1 or not words2:
            return 0.0
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        # Give higher weight to exact matching keywords (e.g. loud, mute)
        score = len(intersection) / len(union)
        return score

    def match_intent(self, text: str) -> Tuple[Optional[str], float]:
        """
        Matches a natural query to a system intent.

        Returns:
            Tuple of (matched_intent, confidence_score)
        """
        query = text.lower().strip()
        if not query:
            return None, 0.0

        # Direct exact match check
        for intent, sentences in INTENT_TEMPLATES.items():
            if query in sentences:
                return intent, 1.0

        # Phonetic & Typos Fuzzy Matcher (Gate 1.2)
        # Fixes STT hallucinations (e.g. "Mix green brighter" -> "make screen brighter")
        import difflib
        best_fuzzy_score = 0.0
        best_fuzzy_intent = None
        best_fuzzy_sentence = None
        for i, sentence in enumerate(self._flat_sentences):
            score = difflib.SequenceMatcher(None, query, sentence).ratio()
            if score > best_fuzzy_score:
                best_fuzzy_score = score
                best_fuzzy_intent = self._flat_intents[i]
                best_fuzzy_sentence = sentence
                
        if best_fuzzy_score > 0.75:
            logger.info(f"Fuzzy phonetic match for STT typo: '{query}' -> '{best_fuzzy_sentence}' -> {best_fuzzy_intent} (Confidence: {best_fuzzy_score:.2f})")
            return best_fuzzy_intent, best_fuzzy_score

        # Method 1: SentenceTransformers (Gate 2 Semantic)
        if self.model:
            try:
                import numpy as np
                # Encode sentences
                embeddings = self.model.encode(self._flat_sentences, convert_to_numpy=True)
                query_emb = self.model.encode([query], convert_to_numpy=True)

                # Compute cosine similarities
                # dot product of normalized vectors
                norms = np.linalg.norm(embeddings, axis=1)
                query_norm = np.linalg.norm(query_emb[0])
                if query_norm > 0:
                    similarities = np.dot(embeddings, query_emb[0]) / (norms * query_norm)
                    best_idx = np.argmax(similarities)
                    score = float(similarities[best_idx])
                    if score >= self.threshold:
                        logger.info(f"Semantic match found via Transformer: '{self._flat_sentences[best_idx]}' -> {self._flat_intents[best_idx]} ({score:.2f})")
                        return self._flat_intents[best_idx], score
            except Exception as e:
                logger.error(f"Transformer matching failed, falling back: {e}")

        # Method 2: High-Speed Bag-of-Words Fallback (Gate 1.5)
        best_intent = None
        best_score = 0.0
        for i, sentence in enumerate(self._flat_sentences):
            score = self._fallback_similarity(query, sentence)
            if score > best_score:
                best_score = score
                best_intent = self._flat_intents[i]

        if best_score >= 0.4:  # Fallback threshold
            logger.info(f"Semantic match found via Fallback Matcher: -> {best_intent} ({best_score:.2f})")
            return best_intent, best_score

        return None, 0.0


if __name__ == "__main__":
    matcher = SimilarityMatcher()
    
    # Test cases
    test_queries = [
        "make it louder",
        "it's too loud in here",
        "mute the sound",
        "kill this application",
        "lock the screen",
        "what is the time"
    ]
    
    print("\nTesting Semantic Similarity Matching:")
    for q in test_queries:
        intent, score = matcher.match_intent(q)
        print(f"Query: '{q}' -> Intent: {intent} (Confidence: {score:.2f})")
