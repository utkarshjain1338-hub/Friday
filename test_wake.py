import asyncio
from voice.wakeword_manager import WakeWordManager
from core.bus import bus

async def main():
    wm = WakeWordManager()
    
    # Listen to wake word events
    bus.on("wake_word_detected", lambda *args, **kwargs: print("BUS EVENT:", args, kwargs))
    
    print("Waiting for wake word...")
    res = await wm.wait_for_wake_word()
    print("Result:", res)

asyncio.run(main())
