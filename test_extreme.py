import asyncio
import time
from loguru import logger
import sys

logger.remove()
logger.add(sys.stdout, format="<level>{level}</level> | {message}", level="DEBUG")

async def test_silence_detector():
    logger.info("--- Testing Layer 2: Silence Detector ---")
    from voice.silence_detector import SilenceDetector
    import numpy as np
    
    detector = SilenceDetector()
    chunk = np.zeros(512, dtype=np.float32)
    silent = detector.is_silent(chunk)
    logger.info(f"Silence correctly detected on zero array: {silent}")
    
    chunk_loud = np.random.uniform(-1.0, 1.0, 512).astype(np.float32)
    loud = detector.is_silent(chunk_loud)
    logger.info(f"Silence correctly NOT detected on loud array: {not loud}")

async def test_browser_controller():
    logger.info("--- Testing Layer 7: Browser Controller ---")
    from automation.browser_controller import PLAYWRIGHT_AVAILABLE, _open_url
    logger.info(f"Playwright Available: {PLAYWRIGHT_AVAILABLE}")
    # We will just see if the import and boolean works, actually opening might spawn tabs.

async def test_semantic_matcher():
    logger.info("--- Testing Layer 4: Semantic Matcher ---")
    from semantic.similarity_matcher import SimilarityMatcher
    matcher = SimilarityMatcher()
    
    # Wait a bit for background thread to load model if available
    await asyncio.sleep(2) 
    
    intent, score = matcher.match_intent("make it way louder in here")
    logger.info(f"Intent for 'make it way louder in here': {intent} (score: {score:.2f})")
    
async def test_ollama():
    logger.info("--- Testing Layer 14: Ollama Client ---")
    from brain.ollama_client import OllamaClient
    client = OllamaClient(model="qwen2.5:0.5b")
    
    avail = await client.is_available()
    logger.info(f"Ollama Available: {avail}")
    
    if avail:
        try:
            logger.info("Attempting generation. This might hang if Ollama is unresponsive...")
            start = time.time()
            resp = await asyncio.wait_for(
                client.generate("Say 'test'"),
                timeout=10.0
            )
            elapsed = time.time() - start
            logger.info(f"Generation successful in {elapsed:.2f}s: {resp}")
        except asyncio.TimeoutError:
            logger.error("Ollama generation TIMED OUT after 10s.")
        except Exception as e:
            logger.error(f"Ollama generation FAILED: {e}")
    else:
        logger.error("Ollama is not available on localhost:11434")

async def test_system_controls():
    logger.info("--- Testing Layer 6: Reflex Engine ---")
    from reflex.system_controls import SystemControls
    controls = SystemControls()
    
    # Just check paths
    logger.info(f"wpctl path: {controls.wpctl_path}")
    logger.info(f"playerctl path: {controls.playerctl_path}")
    logger.info(f"hyprctl path: {controls.hyprctl_path}")
    
async def main():
    logger.info("STARTING EXTREME COMPONENT TEST")
    try:
        await test_silence_detector()
    except Exception as e: logger.error(f"Silence detector failed: {e}")
    
    try:
        await test_browser_controller()
    except Exception as e: logger.error(f"Browser controller failed: {e}")

    try:
        await test_system_controls()
    except Exception as e: logger.error(f"System controls failed: {e}")
    
    try:
        await test_semantic_matcher()
    except Exception as e: logger.error(f"Semantic matcher failed: {e}")
    
    try:
        await test_ollama()
    except Exception as e: logger.error(f"Ollama test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
