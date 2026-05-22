import logging
import json
import time
from collections import defaultdict
import os

logger = logging.getLogger("Friday-AdaptiveLearning")

class AdaptiveLearningEngine:
    def __init__(self, memory_file="adaptive_memory.json"):
        self.memory_file = memory_file
        # Sequence memory: { "App1 -> App2": {"App3": count, "App4": count} }
        self.transitions = defaultdict(lambda: defaultdict(int))
        self.current_session = []
        self.last_event_time = 0
        self.session_timeout = 120 # 2 minutes pause = new session
        
        self._load()

    def _load(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        for next_k, count in v.items():
                            self.transitions[k][next_k] = count
            except Exception as e:
                logger.error(f"Failed to load adaptive memory: {e}")

    def _save(self):
        try:
            with open(self.memory_file, "w") as f:
                json.dump(self.transitions, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save adaptive memory: {e}")

    def record_event(self, event_name: str):
        now = time.time()
        
        # Check if session expired
        if now - self.last_event_time > self.session_timeout:
            self.current_session = []
            
        self.current_session.append(event_name)
        self.last_event_time = now
        
        # Update transition matrix for predictive workflows
        if len(self.current_session) >= 3:
            # We look at the last 3 actions
            context = f"{self.current_session[-3]} -> {self.current_session[-2]}"
            next_action = self.current_session[-1]
            self.transitions[context][next_action] += 1
            self._save()
            
            prediction = self.predict_next(context)
            if prediction and prediction != next_action:
                logger.info(f"Predictive Engine: Based on '{context}', you might next do '{prediction}'.")
                return prediction
        
        return None

    def predict_next(self, context: str):
        if context in self.transitions:
            possibilities = self.transitions[context]
            if not possibilities:
                return None
            
            # Find the most likely next action
            best_next = max(possibilities.items(), key=lambda x: x[1])
            # Only predict if we have seen it at least 3 times
            if best_next[1] >= 3:
                return best_next[0]
        return None
