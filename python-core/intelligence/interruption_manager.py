import logging

logger = logging.getLogger("Friday-InterruptionManager")

class InterruptionManager:
    def __init__(self, state_graph):
        self.state_graph = state_graph
        self.do_not_disturb_categories = ["gaming", "communication", "meeting"]

    def is_safe_to_interrupt(self) -> bool:
        category = self.state_graph.get_current_category()
        
        if category in self.do_not_disturb_categories:
            logger.info(f"InterruptionManager: Blocking proactive action. Active category is '{category}'.")
            return False
            
        # Example logic for fullscreen/meetings could go here when events are added
        return True
