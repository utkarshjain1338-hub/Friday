import argparse
from ui.cli import run_cli, run_voice_mode


def main():
    parser = argparse.ArgumentParser(description="Friday — offline Linux assistant")
    parser.add_argument("--voice", action="store_true", help="Start Friday in voice mode")
    args = parser.parse_args()

    print("Welcome to Friday — your offline Linux assistant.")
    print("Type 'help' for commands or run with --voice for voice mode.")

    if args.voice:
        run_voice_mode()
    else:
        run_cli()


if __name__ == "__main__":
    main()
