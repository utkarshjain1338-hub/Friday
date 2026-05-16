"""Quick-start example showing how to integrate all Friday components."""
import asyncio
import numpy as np
from loguru import logger

# Import all managers
from core.assistant_state import get_state_manager, AssistantMode
from core.diagnostics import get_diagnostics, setup_logging, PerformanceTimer
from voice.device_controller import get_device_controller, AudioOwner
from voice.streaming_transcriber import StreamingTranscriber
from voice.audio_buffer import AudioBuffer
from voice.silence_detector import SilenceDetector
from voice.speech_queue import SpeechQueue
from voice.playback_manager import PlaybackManager
from voice.interrupt_handler import InterruptHandler
from brain.context_manager import get_context_manager
from brain.response_streamer import ResponseStreamer
from brain.token_pipeline import TokenPipeline
from skills.skill_executor import get_skill_executor
from skills.plugin_loader import PluginLoader
from ui.hud import TerminalHUD, SimpleDashboard


async def mock_audio_generator():
    """Mock generator for testing (yields random audio chunks)."""
    for _ in range(100):
        # Generate 512 samples of random noise
        chunk = np.random.randn(512).astype(np.float32) * 0.01
        yield chunk
        await asyncio.sleep(0.01)  # Simulate real-time audio


async def main_loop_example():
    """
    Example of complete Friday assistant main loop.
    
    This demonstrates:
    1. Audio device locking
    2. STT streaming
    3. LLM context management
    4. TTS queueing
    5. Skill execution
    6. Real-time diagnostics
    """
    
    # Setup logging
    setup_logging(log_dir="logs")
    logger.info("Starting Friday Assistant Example")
    
    # Initialize all components
    state_mgr = await get_state_manager()
    device_ctrl = await get_device_controller()
    diag = await get_diagnostics()
    context_mgr = await get_context_manager()
    skill_executor = await get_skill_executor()
    
    # Initialize audio components
    transcriber = StreamingTranscriber()
    speech_queue = SpeechQueue()
    playback_mgr = PlaybackManager()
    interrupt_handler = InterruptHandler()
    token_pipeline = TokenPipeline()
    
    # Initialize UI
    hud = SimpleDashboard() if True else TerminalHUD()  # Use simple dashboard
    hud_task = asyncio.create_task(hud.start(state_mgr, diag))
    
    logger.info("All components initialized")
    
    try:
        # Main loop
        await state_mgr.update_mode(AssistantMode.IDLE)
        iteration = 0
        
        while iteration < 3:  # Run 3 iterations for demo
            iteration += 1
            logger.info(f"=== Iteration {iteration} ===")
            
            # 1. LISTENING STATE
            logger.info("Waiting for wake word or user input...")
            await state_mgr.update_mode(AssistantMode.LISTENING)
            await state_mgr.set_listening(True)
            
            # Acquire microphone
            mic_acquired = await device_ctrl.acquire_microphone(AudioOwner.STT, timeout=5.0)
            if not mic_acquired:
                logger.warning("Could not acquire microphone")
                continue
            
            try:
                # 2. TRANSCRIPTION
                logger.info("Transcribing audio...")
                async with PerformanceTimer("transcription", diag):
                    # Use mock audio generator
                    audio_gen = mock_audio_generator()
                    transcript = await transcriber.transcribe_stream(
                        audio_gen,
                        on_partial=lambda t: logger.info(f"Partial: {t}")
                    )
                
                if not transcript:
                    transcript = "hello"  # Default for demo
                
                logger.info(f"Transcribed: '{transcript}'")
                await state_mgr.record_utterance(transcript)
                await state_mgr.set_listening(False)
                
            finally:
                await device_ctrl.release_microphone(AudioOwner.STT)
            
            # 3. PROCESSING
            logger.info("Processing request...")
            await state_mgr.update_mode(AssistantMode.PROCESSING)
            await state_mgr.set_processing(True)
            
            # Add to context
            await context_mgr.add_user_message(transcript)
            
            # Simulate LLM response (in real app, stream from Ollama)
            response = f"Response to: {transcript}"
            logger.info(f"AI Response: '{response}'")
            await state_mgr.record_response(response)
            await context_mgr.add_assistant_message(response)
            await state_mgr.set_processing(False)
            
            # 4. SPEAKING
            logger.info("Queuing speech response...")
            await state_mgr.update_mode(AssistantMode.SPEAKING)
            await state_mgr.set_speaking(True)
            
            # Queue speech
            speech_req = await speech_queue.enqueue(response, priority=1)
            logger.info(f"Speech request queued: {speech_req.request_id}")
            
            # Get next request from queue
            next_req = await speech_queue.get_next()
            if next_req:
                # Acquire speaker
                spk_acquired = await device_ctrl.acquire_speaker(AudioOwner.TTS, timeout=5.0)
                if spk_acquired:
                    try:
                        logger.info(f"Playing: '{next_req.text}'")
                        # In real app: generate WAV with piper, then play
                        # For now, just mark as completed
                        await speech_queue.mark_completed()
                        logger.info("Speech completed")
                    finally:
                        await device_ctrl.release_speaker(AudioOwner.TTS)
            
            await state_mgr.set_speaking(False)
            
            # 5. Back to listening
            logger.info("Ready for next command...")
            await state_mgr.update_mode(AssistantMode.IDLE)
            await asyncio.sleep(1)
        
        # Show diagnostics
        stats = await diag.get_statistics()
        logger.info(f"Session Statistics: {stats}")
        
    except Exception as e:
        logger.error(f"Main loop error: {e}", exc_info=True)
    finally:
        await state_mgr.update_mode(AssistantMode.IDLE)
        hud.stop()
        logger.info("Friday Assistant Example Complete")


async def skill_execution_example():
    """Example of executing skills with the skill executor."""
    logger.info("=== Skill Execution Example ===")
    
    skill_executor = await get_skill_executor(timeout=10.0)
    
    # Load plugins
    loader = PluginLoader()
    await loader.load_plugins_async()
    
    skills = loader.get_registry().all_skills()
    logger.info(f"Loaded {len(skills)} skills")
    
    # Execute a skill
    if skills:
        skill = skills[0]
        result = await skill_executor.execute(
            skill,
            command="test_command",
            args={"param": "value"}
        )
        logger.info(f"Execution result: {result}")


if __name__ == "__main__":
    # Run main loop example
    asyncio.run(main_loop_example())
    
    # Optionally run skill execution example
    # asyncio.run(skill_execution_example())
