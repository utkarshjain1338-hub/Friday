import subprocess
from security.safe_commands import is_command_allowed


def execute_safe_command(key: str, command: str) -> str:
    if not is_command_allowed(key):
        return "That command is not allowed for safety reasons."

    try:
        completed = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        output = completed.stdout.strip() or completed.stderr.strip()
        return output if output else f"Executed '{command}' successfully."
    except subprocess.CalledProcessError as exc:
        error_message = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        return f"Command failed: {error_message}"
