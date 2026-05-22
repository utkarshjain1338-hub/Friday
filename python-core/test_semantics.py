import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from semantics.embeddings import EmbeddingEngine
from semantics.matcher import IntentMatcher
from semantics.mapper import ContextualMeaningMapper

def test():
    print("Loading Embedding Engine...")
    engine = EmbeddingEngine()
    print("Loading Matcher...")
    matcher = IntentMatcher(engine)
    mapper = ContextualMeaningMapper()
    
    test_utterances = [
        "I really need to lock in right now",
        "pause this video",
        "let's do some programming",
        "clean my computer please"
    ]
    
    for u in test_utterances:
        print(f"\n--- Testing: '{u}' ---")
        match_result = matcher.match(u)
        final_result = mapper.contextualize(u, match_result)
        print("Result:", final_result)

if __name__ == "__main__":
    test()
