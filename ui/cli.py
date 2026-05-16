from core.assistant import FridayAssistant
from voice.audio_manager import AudioManager
import asyncio
import datetime
import urllib.request
import re

async def get_greeting():
    def _fetch():
        time_str = datetime.datetime.now().strftime("%I:%M %p")
        greeting = f"I am listening. It is {time_str}."
        try:
            req = urllib.request.Request("https://wttr.in/?format=1", headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=2) as response:
                weather_str = response.read().decode('utf-8').strip()
                weather_text = re.sub(r'[^\x00-\x7F]+', '', weather_str).strip()
                if weather_text:
                    weather_text = weather_text.replace('+', '').replace('C', ' Celsius').replace('F', ' Fahrenheit')
                    greeting += f" The weather is {weather_text}."
        except Exception:
            pass
        greeting += " How can I help you?"
        return greeting


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

    print("Friday voice mode is active. Type 'stop' to exit.")
    
    # Greet the user when activated to confirm it is running
    await audio.speak("I am online. Just say 'Hey Jarvis' when you need me.")
    
    while True:
        wake = await audio.wait_for_wake_word()
        if not wake:
            print("Wake word not detected. Try again.")
            continue

        print("Wake word detected, listening...")
        greeting = await get_greeting()
        print(f"Assistant: {greeting}")
        await audio.speak(greeting)
        
        command = await audio.listen()
        if not command:
            continue

        if command.lower().strip() in {"stop", "exit", "quit"}:
            print("Stopping voice mode.")
            return

        response = await assistant.handle_text(command)
        print(response)
        await audio.speak(response)
