import logging
from semantics.embeddings import EmbeddingEngine
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import json
import os

logger = logging.getLogger("Friday-MemoryRetrieval")

class MemoryRetrievalLayer:
    def __init__(self, embedding_engine: EmbeddingEngine, memory_db_file="semantic_documents.json"):
        self.engine = embedding_engine
        self.memory_db_file = memory_db_file
        
        # memory_db = [{"content": "...", "metadata": {...}}, ...]
        self.documents = []
        self.document_embeddings = None
        self._load()

    def _load(self):
        if os.path.exists(self.memory_db_file):
            try:
                with open(self.memory_db_file, "r") as f:
                    self.documents = json.load(f)
                    
                if self.documents:
                    texts = [doc["content"] for doc in self.documents]
                    self.document_embeddings = self.engine.encode(texts)
            except Exception as e:
                logger.error(f"Failed to load memory DB: {e}")

    def _save(self):
        try:
            with open(self.memory_db_file, "w") as f:
                json.dump(self.documents, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save memory DB: {e}")

    def ingest_document(self, content: str, metadata: dict):
        logger.info(f"Ingesting new document into semantic memory: {metadata}")
        
        self.documents.append({"content": content, "metadata": metadata})
        self._save()
        
        # Re-encode all (for a production DB, we would just append the embedding)
        texts = [doc["content"] for doc in self.documents]
        self.document_embeddings = self.engine.encode(texts)

    def retrieve(self, query: str, top_k: int = 2) -> list:
        if not self.documents or self.document_embeddings is None:
            return []
            
        query_emb = self.engine.encode([query])
        similarities = cosine_similarity(query_emb, self.document_embeddings)[0]
        
        # Get top K indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.4: # Only return if somewhat relevant
                results.append({
                    "content": self.documents[idx]["content"],
                    "metadata": self.documents[idx]["metadata"],
                    "score": float(similarities[idx])
                })
                
        return results
