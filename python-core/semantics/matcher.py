import logging
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from .embeddings import EmbeddingEngine
from .intent_registry import get_all_intents_and_labels

logger = logging.getLogger("Friday-Matcher")

class IntentMatcher:
    def __init__(self, embedding_engine: EmbeddingEngine):
        self.engine = embedding_engine
        self.sentences, self.labels = get_all_intents_and_labels()
        
        logger.info("Encoding canonical intents...")
        self.reference_embeddings = self.engine.encode(self.sentences)
        logger.info(f"Encoded {len(self.sentences)} reference phrases.")

    def match(self, utterance: str, threshold: float = 0.65) -> dict:
        query_emb = self.engine.encode([utterance])
        similarities = cosine_similarity(query_emb, self.reference_embeddings)[0]
        
        best_idx = np.argmax(similarities)
        best_score = similarities[best_idx]
        best_label = self.labels[best_idx]
        best_match_phrase = self.sentences[best_idx]

        result = {
            "intent": best_label if best_score >= threshold else "unknown",
            "confidence": float(best_score),
            "matched_phrase": best_match_phrase if best_score >= threshold else None,
            "action": "auto_execute" if best_score >= 0.85 else ("ask_confirmation" if best_score >= 0.65 else "fallback")
        }
        
        logger.info(f"Match for '{utterance}': {result}")
        return result
