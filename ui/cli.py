from core.assistant import FridayAssistant
from voice.audio_manager import AudioManager
import asyncio
import datetime
import urllib.request
import re


def tts_clean(text: str) -> str:
    """Strip markup tags injected by the personality layer before sending to TTS.

    The response humanizer adds tokens like [pause:short], [pause:long] which
    Piper would read aloud literally. Strip them here.
    """
    # Remove [tag:value] and [tag] tokens
    text = re.sub(r'\[\w+(?::\w+)?\]', '', text)
    # Remove any leftover XML/SSML-style tags
    text = re.sub(r'<[^>]+>', '', text)
    # Collapse multiple whitespace/newlines
    text = re.sub(r'\s+', ' ', text).strip()
    return text


async def get_greeting():
    def _fetch():
        time_str = datetime.datetime.now().strftime("%I:%M %p")
        greeting = f"I am listening. It is {time_str}."
        try:
            # Use explicit format string to get plain text: temperature + condition
            # e.g. "+32°C Sunny" — avoid ?format=1 which can return HTML
            req = urllib.request.Request(
                "https://wttr.in/?format=%t+%C",
                headers={'User-Agent': 'curl/7.0'}  # wttr.in returns plain text for curl UA
            )
            with urllib.request.urlopen(req, timeout=1) as response:
                weather_raw = response.read().decode('utf-8').strip()
                # Strip any HTML tags in case we still get markup
                weather_clean = re.sub(r'<[^>]+>', '', weather_raw)
                # Keep only printable ASCII for TTS
                weather_text = re.sub(r'[^\x20-\x7E]', '', weather_clean).strip()
                # Sanity check: ignore if it looks like HTML or is too long
                if weather_text and '<' not in weather_text and len(weather_text) < 80:
                    # Make it more speakable: "+32C" → "32 Celsius"
                    weather_text = re.sub(r'[+]', '', weather_text)
                    weather_text = re.sub(r'(\d+)C\b', r'\1 Celsius', weather_text)
                    weather_text = re.sub(r'(\d+)F\b', r'\1 Fahrenheit', weather_text)
                    greeting += f" The weather is {weather_text}."
        except Exception:
            pass
        greeting += " How can I help you?"
        return greeting

    return await asyncio.to_thread(_fetch)


def print_help():
    print("Friday CLI commands:")
    print("  help               Show this help text")
    print("  listen             Record audio and transcribe it to a command")
    print("  history            Show recent typed commands")
    print("  exit, quit, bye    Exit Friday")
    print("  voice mode         Enter wake-word driven voice mode")
    print("  Any other text will be handled as a command or question.")


async def run_cli():
    assistant = FridayAssistant()
    audio = AudioManager()

    print("Friday CLI ready. Type 'help' for commands.")
    while True:
        user_input = (await asyncio.to_thread(input, "Friday> ")).strip()
        if user_input.lower() in {"exit", "quit", "bye"}:
            print("Goodbye from Friday. Stay safe!")
            break

        if not user_input:
            continue

        if user_input.lower() == "help":
            print_help()
            continue

        if user_input.lower() == "listen":
            print("Listening for audio input...")
            command = await audio.listen()
            print(f"Heard: {command}")
            response = await assistant.handle_text(command)
            print(response)
            continue

        if user_input.lower() == "voice mode":
            await run_voice_mode()
            continue

        response = await assistant.handle_text(user_input)
        print(response)


async def run_voice_mode():
    assistant = FridayAssistant()
    audio = AudioManager()

    print("Friday voice mode is active. Say 'Hey Friday' to wake up, 'stop' to exit.")

    # Greet the user when activated to confirm it is running
    await audio.speak("I am online. Just say Hey Friday when you need me.")

    import tempfile, pathlib
    loop = asyncio.get_running_loop()
    wm = audio.wakeword

    while True:
        wake = await audio.wait_for_wake_word()
        if not wake:
            print("Wake word not detected. Listening again.")
            continue

        print("Wake word detected, listening...")
        greeting = await get_greeting()
        print(f"Assistant: {greeting}")
        await audio.speak(greeting)

        active_loop = True
        consecutive_silent = 0

        while active_loop:
            print("[ Listening for your command... ]")
            try:
                # Record command — use the wakeword manager's reliable recorder
                # (fixed 5-second window at 16 kHz via PipeWire-pulse)
                raw = await loop.run_in_executor(None, wm._record_seconds, 5.0)
            except Exception as exc:
                print(f"Recording error: {exc}")
                break

            # Save and transcribe
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = pathlib.Path(tmp.name)
            await loop.run_in_executor(None, wm._save_wav, raw, str(tmp_path))

            command = await audio.stt.transcribe_file(str(tmp_path))
            try:
                tmp_path.unlink()
            except Exception:
                pass

            if not command or not command.strip() or len(command.strip()) <= 1:
                consecutive_silent += 1
                if consecutive_silent >= 2:
                    print("[ Idle detected — returning to wake word mode ]")
                    await audio.speak("Going to sleep. Just say Hey Friday when you need me.")
                    active_loop = False
                continue

            consecutive_silent = 0
            command = command.strip()
            print(f"You said: {command}")

            normalized_cmd = command.lower()
            if any(sleep_word in normalized_cmd for sleep_word in ["go to sleep", "sleep", "goodbye", "bye", "stop"]):
                await audio.speak("Going to sleep now.")
                print("Returning to wake-word mode.")
                active_loop = False
                break

            if normalized_cmd in {"exit", "quit"}:
                await audio.speak("Goodbye!")
                print("Stopping voice mode.")
                return

            response = await assistant.handle_text(command)
            spoken = tts_clean(response)
            print(f"Friday: {spoken}")
            await audio.speak(spoken)
