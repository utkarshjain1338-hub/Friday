"""Memory subsystem for Friday with Episodic, Semantic, and Procedural memory."""

try:
    from .retrieval import MemoryRetrievalLayer
    __all__ = ["MemoryRetrievalLayer"]
except ImportError:
    # sklearn / sentence-transformers not installed — RAG retrieval unavailable
    MemoryRetrievalLayer = None  # type: ignore
    __all__ = []
