import logging
from .state_graph import StateGraph
from .interruption_manager import InterruptionManager
from .workflow_predictor import WorkflowPredictor
from .synthesizer import ProceduralSynthesizer

logger = logging.getLogger("Friday-DecisionEngine")

class DecisionEngine:
    def __init__(self, adaptive_engine, event_router):
        self.router = event_router
        self.state_graph = StateGraph()
        self.interruption_manager = InterruptionManager(self.state_graph)
        self.predictor = WorkflowPredictor(adaptive_engine, self.state_graph)
        self.synthesizer = ProceduralSynthesizer()

    async def handle_event(self, event_signature: str, context: dict = None):
        """Processes an event, predicts workflow, ranks safety, and synthesizes output deterministically."""
        # 1. Update State Graph
        if context:
            for k, v in context.items():
                self.state_graph.update_node(k, v)
                
        # 2. Predict Workflow
        predicted_workflow = self.predictor.predict(event_signature)
        if not predicted_workflow:
            return

        logger.info(f"DecisionEngine: Predicted workflow '{predicted_workflow}'")

        # 3. Check Interruption Safety
        if not self.interruption_manager.is_safe_to_interrupt():
            logger.info("DecisionEngine: Aborting execution due to interruption safety constraints.")
            return

        # 4. Synthesize Response
        speech_text = self.synthesizer.synthesize(predicted_workflow, self.state_graph.current_state)
        
        # 5. Route to EventBus
        logger.info(f"DecisionEngine: Executing and announcing -> {speech_text}")
        await self.router.route({"TTS_Speak": {"text": speech_text}})
        
        # Optionally, trigger the actual workflow here if it's a known canonical workflow
        # await self.router.route({"WorkflowTriggered": {"name": predicted_workflow}})
