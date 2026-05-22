import logging
import numpy as np
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None
    logging.warning("sentence-transformers not installed. Embeddings will not work.")

logger = logging.getLogger("Friday-Embeddings")

class EmbeddingEngine:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self._load_model()

    def _load_model(self):
        if SentenceTransformer is not None:
            logger.info(f"Loading embedding model: {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Model loaded successfully.")
        else:
            logger.error("Cannot load model, sentence-transformers missing.")

    def encode(self, texts):
        if self.model is None:
            return np.zeros((len(texts) if isinstance(texts, list) else 1, 384))
        return self.model.encode(texts, convert_to_numpy=True)
