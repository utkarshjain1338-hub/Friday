import yaml
from pathlib import Path
from automation.command_executor import execute_safe_command
from automation.linux_controller import (
    focus_window,
    kill_process,
    list_processes,
    open_application,
)
from automation.system_monitor import get_system_report
from automation.file_manager import (
    create_folder,
    delete_path,
    list_home,
    move_file,
    search_files,
)
from automation.browser_controller import (
    open_website,
    open_youtube,
    search_google,
)
from brain.llm import FridayLLM
from loguru import logger


class FridayRouter:
    def __init__(self):
        self.config = self._load_config()
        self.llm = FridayLLM()
        logger.info("Router initialized with config.")

    def _load_config(self):
        path = Path(__file__).parent.parent / "config" / "commands.yaml"
        with open(path, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)

    def route(self, text: str) -> str:
        normalized = text.lower().strip()
        safe_commands = self.config.get("safe_commands", {})

        if normalized in safe_commands:
            command = safe_commands[normalized]
            return execute_safe_command(normalized, command)

        if "open firefox" in normalized or "launch firefox" in normalized:
            return open_application("firefox")

        if "open code" in normalized or "launch vscode" in normalized or "launch code" in normalized:
            return open_application("code")

        if "open terminal" in normalized or "launch terminal" in normalized:
            return open_application("terminal")

        if "open browser" in normalized or "open website" in normalized:
            target = self._extract_parameter(normalized, "open website") or self._extract_parameter(normalized, "open browser")
            return open_website(target or "https://www.google.com")

        if "search google" in normalized:
            query = self._extract_parameter(normalized, "search google")
            return search_google(query)

        if "youtube" in normalized:
            if "search" in normalized:
                query = self._extract_parameter(normalized, "search youtube")
                return open_youtube(query)
            return open_youtube()

        if "battery" in normalized or "cpu" in normalized or "memory" in normalized or "system report" in normalized:
            return get_system_report()

        if "list home files" in normalized or "show home files" in normalized:
            return list_home()

        if "search file" in normalized or "find file" in normalized:
            query = self._extract_parameter(normalized, "search file") or self._extract_parameter(normalized, "find file")
            return search_files(query)

        if "create folder" in normalized or "make folder" in normalized:
            target = self._extract_parameter(normalized, "create folder") or self._extract_parameter(normalized, "make folder")
            return create_folder(target)

        if "move file" in normalized and " to " in normalized:
            source, target = normalized.split(" to ", 1)
            source = source.replace("move file", "", 1).strip()
            target = target.strip()
            return move_file(source, target)

        if "delete" in normalized or "remove" in normalized:
            target = self._extract_parameter(normalized, "delete") or self._extract_parameter(normalized, "remove")
            return delete_path(target)

        if "close" in normalized or "kill" in normalized:
            target = self._extract_parameter(normalized, "close") or self._extract_parameter(normalized, "kill")
            return kill_process(target)

        if "list processes" in normalized or "running processes" in normalized:
            return list_processes()

        if any(keyword in normalized for keyword in ["help", "what", "who", "how", "tell"]):
            return self.llm.ask(text)

        return (
            "I did not understand that yet. Try a safe command like 'open firefox', 'show battery status', "
            "or ask for help."
        )

    def _extract_parameter(self, text: str, phrase: str) -> str:
        if phrase not in text:
            return ""
        return text.split(phrase, 1)[1].strip()
