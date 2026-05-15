from core.assistant import FridayAssistant
from voice.audio_manager import AudioManager


def print_help():
    print("Friday CLI commands:")
    print("  help               Show this help text")
    print("  listen             Record audio and transcribe it to a command")
    print("  history            Show recent typed commands")
    print("  exit, quit, bye    Exit Friday")
    print("  Any other text will be handled as a command or question.")


def run_cli():
    assistant = FridayAssistant()
    audio = AudioManager()

    print("Friday CLI ready. Type 'help' for commands.")
    while True:
        user_input = input("Friday> ").strip()
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
            command = audio.listen()
            print(f"Heard: {command}")
            response = assistant.handle_text(command)
            print(response)
            continue

        if user_input.lower() == "voice mode":
            run_voice_mode()
            continue

        response = assistant.handle_text(user_input)
        print(response)


def run_voice_mode():
    assistant = FridayAssistant()
    audio = AudioManager()

    print("Friday voice mode is active. Type 'stop' to exit.")
    while True:
        if not audio.wait_for_wake_word():
            print("Wake word not detected. Try again.")
            continue

        print("Wake word detected, listening...")
        command = audio.listen()
        if command.lower().strip() in {"stop", "exit", "quit"}:
            print("Stopping voice mode.")
            return

        response = assistant.handle_text(command)
        print(response)
        audio.speak(response)
