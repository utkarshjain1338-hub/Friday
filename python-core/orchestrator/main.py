import asyncio
import json
import logging
from typing import Callable, Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Friday-Orchestrator")

class EventRouter:
    def __init__(self):
        self.handlers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable):
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)

    async def route(self, event: dict):
        # The Rust side serializes enum as a string or dict. 
        # Example: "SystemWake" or {"WindowChanged": {"title": "...", "app": "..."}}
        if isinstance(event, str):
            event_type = event
            payload = {}
        elif isinstance(event, dict):
            event_type = list(event.keys())[0]
            payload = event[event_type]
        else:
            return

        logger.info(f"Routing Event: {event_type} - {payload}")
        if event_type in self.handlers:
            for handler in self.handlers[event_type]:
                if asyncio.iscoroutinefunction(handler):
                    await handler(payload)
                else:
                    handler(payload)

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflows.manager import setup_workflows

from semantics.embeddings import EmbeddingEngine
from semantics.matcher import IntentMatcher
from semantics.mapper import ContextualMeaningMapper
from semantics.semantic_memory import SemanticMemory
from learning.adaptive import AdaptiveLearningEngine
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from memory.retrieval import MemoryRetrievalLayer
from voice.tts_engine import TTSEngine
from intelligence.decision_engine import DecisionEngine

class FridayOrchestrator:
    def __init__(self, event_bus_host: str = "127.0.0.1", event_bus_port: int = 5555):
        self.host = event_bus_host
        self.port = event_bus_port
        self.router = EventRouter()
        
        # Initialize Semantic Intelligence Layer
        self.embedding_engine = EmbeddingEngine()
        self.matcher = IntentMatcher(self.embedding_engine)
        self.mapper = ContextualMeaningMapper()
        self.memory = SemanticMemory()
        self.retrieval_layer = MemoryRetrievalLayer(self.embedding_engine)
        
        # Initialize Audio
        self.tts = TTSEngine()
        
        # Initialize Adaptive Learning Layer
        self.adaptive_engine = AdaptiveLearningEngine()
        
        # Initialize Decision Engine (Deterministic Phase 4)
        self.decision_engine = DecisionEngine(self.adaptive_engine, self.router)
        
        self._setup_default_routes()
        setup_workflows(self.router)

    def _setup_default_routes(self):
        self.router.subscribe("SystemWake", self._on_system_wake)
        self.router.subscribe("UserStartedSpeaking", self._on_speaking_start)
        self.router.subscribe("SpeechRecognized", self._on_speech_recognized)
        self.router.subscribe("WindowChanged", self._on_window_changed)
        self.router.subscribe("MusicStarted", self._on_music_started)
        self.router.subscribe("MusicPaused", self._on_music_paused)
        self.router.subscribe("TTS_Speak", self._on_tts_speak)

    async def _on_system_wake(self, payload):
        logger.info("System Wake Event Handled! Initializing Python subsystems...")

    async def _on_speaking_start(self, payload):
        logger.info("User started speaking. Preparing semantic intent analyzer...")

    async def _on_window_changed(self, payload):
        app = payload.get("app", "")
        title = payload.get("title", "")
        logger.info(f"Context Update -> Window Changed: {app} - {title}")
        self.mapper.update_state("active_app", app)
        self.mapper.update_state("active_title", title)
        
        # Dispatch to deterministic decision engine
        await self.decision_engine.handle_event(
            f"App:{app}", 
            context={"active_app": app, "active_title": title}
        )
        
    async def _on_music_started(self, payload):
        logger.info("Context Update -> Music Started")
        self.mapper.update_state("media_playing", True)
        
    async def _on_music_paused(self, payload):
        logger.info("Context Update -> Music Paused")
        self.mapper.update_state("media_playing", False)
        
    async def _on_tts_speak(self, payload):
        text = payload.get("text", "")
        if text:
            logger.info(f"Friday speaking: {text}")
            await self.tts.speak(text)
        
    async def _on_speech_recognized(self, payload):
        utterance = payload.get("text", "")
        if not utterance: return
        
        logger.info(f"Speech Recognized: {utterance}")
        
        # 1. Match Intent
        match_result = self.matcher.match(utterance)
        
        # 2. Contextualize Meaning
        contextualized_result = self.mapper.contextualize(utterance, match_result)
        
        logger.info(f"Final Semantic Interpretation: {contextualized_result}")
        
        # 3. Execute or ask confirmation
        action = contextualized_result.get("action")
        intent = contextualized_result.get("intent")
        
        if action == "auto_execute" and intent != "unknown":
            # Fire Workflow Trigger
            await self.router.route({"WorkflowTriggered": {"name": intent}})
        elif action == "ask_confirmation":
            logger.info(f"Please confirm: Did you mean '{intent}'? (Similarity: {contextualized_result['confidence']:.2f})")
        else:
            logger.info("Intent unclear. Falling back to generic conversational reasoning or ignoring.")

    async def connect_to_eventbus(self):
        while True:
            try:
                reader, writer = await asyncio.open_connection(self.host, self.port)
                logger.info(f"Connected to Rust EventBus at {self.host}:{self.port}")
                
                while True:
                    data = await reader.readline()
                    if not data:
                        break
                    
                    try:
                        event = json.loads(data.decode().strip())
                        await self.router.route(event)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON received: {data}")
                        
            except ConnectionRefusedError:
                logger.warning("EventBus connection refused. Retrying in 2 seconds...")
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"EventBus connection error: {e}")
                await asyncio.sleep(2)

    async def start_websocket_server(self):
        import websockets
        import json
        
        async def handle_browser(websocket):
            logger.info("Browser Extension Connected!")
            try:
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        event_type = data.get("event")
                        payload = data.get("payload", {})
                        
                        if event_type == "BrowserContextUpdated":
                            logger.info(f"Received Browser Context: {payload.get('url')}")
                            self.mapper.update_state("browser_url", payload.get("url"))
                            self.mapper.update_state("browser_content", payload.get("content"))
                            
                            # Auto-ingest browser content into Semantic Memory for RAG
                            if payload.get("content"):
                                self.retrieval_layer.ingest_document(
                                    content=payload.get("content"),
                                    metadata={"url": payload.get("url"), "source": "browser"}
                                )
                                
                            await self.decision_engine.handle_event(
                                f"Browser:{payload.get('url')}",
                                context={"browser_url": payload.get("url")}
                            )
                        elif event_type == "BrowserTabChanged":
                            logger.info(f"Browser Tab Changed: {payload.get('title')}")
                            self.mapper.update_state("browser_url", payload.get("url"))
                            self.mapper.update_state("browser_title", payload.get("title"))
                            
                            await self.decision_engine.handle_event(
                                f"Browser:{payload.get('url')}",
                                context={"browser_url": payload.get("url")}
                            )
                    except Exception as e:
                        logger.error(f"Error handling browser message: {e}")
            except websockets.exceptions.ConnectionClosed:
                logger.info("Browser Extension Disconnected.")

        logger.info("Starting WebSocket server on ws://127.0.0.1:5556")
        async with websockets.serve(handle_browser, "127.0.0.1", 5556):
            await asyncio.Future()  # run forever

    async def start(self):
        logger.info("Starting Friday Orchestrator (Python)...")
        await asyncio.gather(
            self.connect_to_eventbus(),
            self.start_websocket_server()
        )

if __name__ == "__main__":
    orchestrator = FridayOrchestrator()
    asyncio.run(orchestrator.start())
