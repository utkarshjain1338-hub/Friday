import yaml
from pathlib import Path


def _load_safe_commands():
    path = Path(__file__).parent.parent / "config" / "commands.yaml"
    with open(path, "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    return set(config.get("safe_commands", {}).keys())


SAFE_COMMAND_KEYS = _load_safe_commands()


def is_command_allowed(command_key: str) -> bool:
    return command_key in SAFE_COMMAND_KEYS
