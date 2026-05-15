import subprocess


def open_application(command: str) -> str:
    try:
        subprocess.Popen(command.split())
        return f"Launching {command}."
    except Exception as exc:
        return f"Could not launch {command}: {exc}"
