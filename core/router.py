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
from brain.reasoning_agent import ReasoningAgent
from brain.memory_reasoning_engine import MemoryReasoningEngine
from memory.enhanced_memory import EnhancedMemoryDatabase
from tools.tool_loader import create_tool_system
from loguru import logger
import asyncio
from skills.registry import SkillRegistry
from skills.loader import discover_plugins
from security.validator import assess_command_risk, requires_confirmation
from security.permission_manager import PermissionManager


class FridayRouter:
    def __init__(self):
        self.config = self._load_config()
        
        # Initialize enhanced memory system
        try:
            self.memory_db = EnhancedMemoryDatabase()
            self.memory_engine = MemoryReasoningEngine(self.memory_db)
            logger.info("Enhanced memory system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize memory system: {e}")
            self.memory_db = None
            self.memory_engine = None
        
        # Initialize tool system
        try:
            self.tool_registry, self.tool_orchestrator = create_tool_system()
            logger.info(f"Loaded {len(self.tool_registry.list_tools())} tools")
        except Exception as e:
            logger.error(f"Failed to initialize tool system: {e}")
            self.tool_registry = None
            self.tool_orchestrator = None
        
        # Initialize LLM with tool registry
        self.llm = FridayLLM(tool_registry=self.tool_registry)
        
        # Initialize reasoning agent
        if self.tool_orchestrator:
            self.reasoning_agent = ReasoningAgent(self.llm, self.tool_orchestrator)
        else:
            self.reasoning_agent = None
        
        # plugin registry
        self.registry = SkillRegistry()
        try:
            discover_plugins(self.registry)
        except Exception:
            logger.warning("Failed to discover plugins")
        self.permission_manager = PermissionManager()
        logger.info("Router initialized with config, tool system, and enhanced memory.")

    def _load_config(self):
        path = Path(__file__).parent.parent / "config" / "commands.yaml"
        with open(path, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)

    async def route(self, text: str) -> str:
        import datetime as _dt
        normalized = text.lower().strip()

        # ----------------------------------------------------------------
        # Fast built-in handlers (no LLM needed)
        # ----------------------------------------------------------------
        if any(p in normalized for p in ["what time", "current time", "what's the time", "whats the time"]):
            now = _dt.datetime.now().strftime("%I:%M %p")
            return f"It is {now}."

        if any(p in normalized for p in ["what date", "today's date", "todays date", "what day", "what is today"]):
            today = _dt.datetime.now().strftime("%A, %B %d, %Y")
            return f"Today is {today}."

        if any(p in normalized for p in ["hello", "hi friday", "hey", "good morning", "good evening", "good afternoon"]):
            hour = _dt.datetime.now().hour
            greet = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")
            return f"{greet}! How can I help you?"

        # plugin skills first
        try:
            matches = self.registry.find_for_command(normalized)
            if matches:
                # execute first matching skill
                skill = matches[0]
                try:
                    result = await skill.execute(text, {"text": text})
                    return result
                except Exception as exc:
                    logger.exception("Skill execution failed: %s", exc)
                    return "Skill execution failed."
        except Exception:
            pass
        safe_commands = self.config.get("safe_commands", {})

        if normalized in safe_commands:
            command = safe_commands[normalized]
            # execute_safe_command is synchronous; run in thread
            # check risk
            risk, reason = assess_command_risk(command)
            if requires_confirmation(risk) and not self.permission_manager.is_granted(command):
                # interactive confirmation required
                loop = asyncio.get_running_loop()
                confirm = await loop.run_in_executor(None, input, f"Confirm execution of '{command}'? (yes/no): ")
                if confirm.strip().lower() != "yes":
                    return "Command cancelled by user."
                self.permission_manager.grant(command)

            return await asyncio.to_thread(execute_safe_command, normalized, command)

        if "open firefox" in normalized or "launch firefox" in normalized:
            return await asyncio.to_thread(open_application, "firefox")

        if "open code" in normalized or "launch vscode" in normalized or "launch code" in normalized:
            return await asyncio.to_thread(open_application, "code")

        if "open terminal" in normalized or "launch terminal" in normalized:
            return await asyncio.to_thread(open_application, "terminal")

        if "open browser" in normalized or "open website" in normalized:
            target = self._extract_parameter(normalized, "open website") or self._extract_parameter(normalized, "open browser")
            return await asyncio.to_thread(open_website, target or "https://www.google.com")

        if "search google" in normalized:
            query = self._extract_parameter(normalized, "search google")
            return await asyncio.to_thread(search_google, query)

        if "youtube" in normalized:
            if "search" in normalized:
                query = self._extract_parameter(normalized, "search youtube")
                return await asyncio.to_thread(open_youtube, query)
            return await asyncio.to_thread(open_youtube)

        if "battery" in normalized or "cpu" in normalized or "memory" in normalized or "system report" in normalized:
            raw = await asyncio.to_thread(get_system_report)
            return await self.llm.ask(f"Please summarize this system status naturally in 1-2 short sentences for speech: {raw}")

        if "list home files" in normalized or "show home files" in normalized:
            raw = await asyncio.to_thread(list_home)
            return await self.llm.ask(f"Please summarize these files naturally in 1-2 short sentences: {raw}")

        if "search file" in normalized or "find file" in normalized:
            query = self._extract_parameter(normalized, "search file") or self._extract_parameter(normalized, "find file")
            raw = await asyncio.to_thread(search_files, query)
            return await self.llm.ask(f"Please summarize these search results naturally: {raw}")

        if "create folder" in normalized or "make folder" in normalized:
            target = self._extract_parameter(normalized, "create folder") or self._extract_parameter(normalized, "make folder")
            raw = await asyncio.to_thread(create_folder, target)
            return await self.llm.ask(f"Please confirm this action naturally: {raw}")

        if "move file" in normalized and " to " in normalized:
            source, target = normalized.split(" to ", 1)
            source = source.replace("move file", "", 1).strip()
            target = target.strip()
            raw = await asyncio.to_thread(move_file, source, target)
            return await self.llm.ask(f"Please confirm this file move naturally: {raw}")

        if "delete" in normalized or "remove" in normalized:
            target = self._extract_parameter(normalized, "delete") or self._extract_parameter(normalized, "remove")
            raw = await asyncio.to_thread(delete_path, target)
            return await self.llm.ask(f"Please confirm this deletion naturally: {raw}")

        if "close" in normalized or "kill" in normalized:
            target = self._extract_parameter(normalized, "close") or self._extract_parameter(normalized, "kill")
            raw = await asyncio.to_thread(kill_process, target)
            return await self.llm.ask(f"Please confirm this process termination naturally: {raw}")

        if "list processes" in normalized or "running processes" in normalized:
            raw = await asyncio.to_thread(list_processes)
            return await self.llm.ask(f"Please summarize the running processes in 1-2 short sentences naturally: {raw}")

        # For complex requests, use reasoning agent with tool calling
        if self.reasoning_agent and any(keyword in normalized for keyword in ["help", "what", "who", "how", "tell", "can you", "could you", "please"]):
            try:
                logger.info("Using reasoning agent for complex request")
                return await self.reasoning_agent.reason_and_act(text)
            except Exception as e:
                logger.error(f"Reasoning agent failed: {e}")
                return await self.llm.ask(text)
        
        # Fallback to LLM for unclear requests
        if any(keyword in normalized for keyword in ["help", "what", "who", "how", "tell"]):
            return await self.llm.ask(text)

        return (
            "I did not understand that yet. Try a safe command like 'open firefox', 'show battery status', "
            "or ask for help."
        )

    def _extract_parameter(self, text: str, phrase: str) -> str:
        if phrase not in text:
            return ""
        return text.split(phrase, 1)[1].strip()
