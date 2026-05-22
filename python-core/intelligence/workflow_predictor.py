import logging

logger = logging.getLogger("Friday-WorkflowPredictor")

class WorkflowPredictor:
    def __init__(self, adaptive_engine, state_graph):
        self.adaptive = adaptive_engine
        self.state_graph = state_graph

    def predict(self, recent_event_signature: str) -> str:
        """
        Takes the recent event signature (e.g. 'App:code') and checks the Markov 
        chain for a high-probability workflow mapping.
        """
        # Query the underlying adaptive Markov chain
        prediction = self.adaptive.record_event(recent_event_signature)
        
        if prediction:
            # Map low-level predictions to canonical workflows
            # e.g., if predicted next app is "alacritty" and current is "code", we predict "coding_mode"
            current_cat = self.state_graph.get_current_category()
            if current_cat == "development" and "alacritty" in prediction.lower():
                return "coding_mode"
            
            # Direct mapping from learned habits
            if "spotify" in prediction.lower():
                return "media_play"
                
            return prediction
            
        return None
