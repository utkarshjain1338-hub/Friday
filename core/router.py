import os
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
from intents.intent_classifier import IntentClassifier
from learning.adaptive_learner import AdaptiveLearner
from memory.enhanced_memory import EnhancedMemoryDatabase
from system_state.context_monitor import ContextMonitor
from tools.tool_loader import create_tool_system
from workflows.workflow_engine import WorkflowEngine
from loguru import logger
import asyncio
from skills.registry import SkillRegistry
from skills.loader import discover_plugins
from security.validator import assess_command_risk, requires_confirmation
from security.permission_manager import PermissionManager
from reflex.system_controls import SystemControls
from system_state.activity_tracker import ActivityTracker
from semantic.similarity_matcher import SimilarityMatcher


class FridayRouter:
    def __init__(self):
        self.config = self._load_config()
        self.system_controls = SystemControls()
        self.activity_tracker = ActivityTracker()
        self.context_monitor = ContextMonitor()
        self.intent_classifier = IntentClassifier()
        self.workflow_engine = WorkflowEngine()
        self.learning_engine = AdaptiveLearner()
        self.similarity_matcher = SimilarityMatcher()

        
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
        
        # Optional no-LLM mode for pure procedural intelligence
        self.no_llm_mode = os.getenv("NO_LLM_MODE", "false").strip().lower() in ("1", "true", "yes", "on")
        if self.no_llm_mode:
            self.llm = None
            self.reasoning_agent = None
            logger.info("No-LLM mode enabled: Friday will use semantic and procedural intelligence only.")
        else:
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
        self.learning_engine.track_command(text)

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

        # ----------------------------------------------------------------
        # GATE 1: REFLEX LAYER (0ms execution Wayland Native)
        # ----------------------------------------------------------------
        # Volume controls
        if any(p in normalized for p in ["toggle mute", "mute system", "unmute system", "toggle sound", "mute volume", "mute the volume"]) or normalized == "mute":
            return await self.system_controls.toggle_mute()
        if any(p in normalized for p in ["volume up", "raise volume", "increase volume", "louder"]):
            return await self.system_controls.volume_up()
        if any(p in normalized for p in ["volume down", "lower volume", "decrease volume", "quieter"]):
            return await self.system_controls.volume_down()

        # Media controls
        if any(p in normalized for p in ["play pause", "toggle playback", "play music", "pause music"]) or normalized in ["play", "pause"]:
            return await self.system_controls.media_play_pause()
        if any(p in normalized for p in ["next song", "next track", "skip song"]):
            return await self.system_controls.media_next()
        if any(p in normalized for p in ["previous song", "prev song", "previous track"]):
            return await self.system_controls.media_previous()

        # Window & Screen controls
        if any(p in normalized for p in ["close this window", "close window", "kill active window", "close active window"]):
            return await self.system_controls.close_active_window()
        if any(p in normalized for p in ["lock screen", "lock session", "lock pc"]):
            return await self.system_controls.lock_screen()

        # Workspace controls
        import re
        ws_match = re.search(r"workspace\s+(\d+)", normalized)
        if ws_match:
            ws_num = ws_match.group(1)
            return await self.system_controls.switch_workspace(ws_num)
        if "next workspace" in normalized:
            return await self.system_controls.next_workspace()
        if "previous workspace" in normalized or "prev workspace" in normalized:
            return await self.system_controls.prev_workspace()

        # Window state triggers
        if any(p in normalized for p in ["toggle fullscreen", "fullscreen window", "go fullscreen"]):
            return await self.system_controls.toggle_fullscreen()
        if any(p in normalized for p in ["toggle floating", "float window"]):
            return await self.system_controls.toggle_floating()

        # Hardware & Power triggers
        if any(p in normalized for p in ["mute mic", "unmute mic", "toggle microphone", "toggle mic"]):
            return await self.system_controls.toggle_mic_mute()
        if any(p in normalized for p in ["increase brightness", "brightness up", "brighten screen"]):
            return await self.system_controls.brightness_up()
        if any(p in normalized for p in ["decrease brightness", "brightness down", "dim screen"]):
            return await self.system_controls.brightness_down()
        if any(p in normalized for p in ["suspend system", "system sleep", "put computer to sleep", "suspend pc"]):
            return await self.system_controls.system_suspend()
        if any(p in normalized for p in ["reboot system", "restart pc", "reboot pc"]):
            return await self.system_controls.system_reboot()
        if any(p in normalized for p in ["shutdown system", "power off pc", "turn off pc", "shutdown pc"]):
            return await self.system_controls.system_shutdown()

        # ----------------------------------------------------------------
        # Workflow routing and intent classification
        # ----------------------------------------------------------------
        intent_name, intent_category, intent_score = self.intent_classifier.classify(text)
        logger.info(f"Intent classifier: {intent_name} / {intent_category} (score {intent_score:.2f})")
        if intent_name in self.workflow_engine.list_workflows():
            return await self.workflow_engine.execute_workflow(intent_name)

        # ----------------------------------------------------------------
        # GATE 2: SEMANTIC LAYER (100ms execution NLP similarity matcher)
        # ----------------------------------------------------------------
        intent, confidence = self.similarity_matcher.match_intent(text)
        if intent and confidence >= 0.4:
            logger.info(f"Matched semantic intent '{intent}' with confidence {confidence:.2f} for query '{text}'")
            if intent == "toggle_mute":
                return await self.system_controls.toggle_mute()
            elif intent == "volume_up":
                return await self.system_controls.volume_up()
            elif intent == "volume_down":
                return await self.system_controls.volume_down()
            elif intent == "media_play_pause":
                return await self.system_controls.media_play_pause()
            elif intent == "media_next":
                return await self.system_controls.media_next()
            elif intent == "media_previous":
                return await self.system_controls.media_previous()
            elif intent == "close_active_window":
                return await self.system_controls.close_active_window()
            elif intent == "lock_screen":
                return await self.system_controls.lock_screen()
            elif intent == "next_workspace":
                return await self.system_controls.next_workspace()
            elif intent == "prev_workspace":
                return await self.system_controls.prev_workspace()
            elif intent == "toggle_fullscreen":
                return await self.system_controls.toggle_fullscreen()
            elif intent == "toggle_floating":
                return await self.system_controls.toggle_floating()
            elif intent == "toggle_mic_mute":
                return await self.system_controls.toggle_mic_mute()
            elif intent == "brightness_up":
                return await self.system_controls.brightness_up()
            elif intent == "brightness_down":
                return await self.system_controls.brightness_down()
            elif intent == "system_suspend":
                return await self.system_controls.system_suspend()
            elif intent == "system_reboot":
                return await self.system_controls.system_reboot()
            elif intent == "system_shutdown":
                return await self.system_controls.system_shutdown()



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
            query = ""
            if "search youtube for " in normalized:
                query = self._extract_parameter(normalized, "search youtube for ")
            elif "search youtube " in normalized:
                query = self._extract_parameter(normalized, "search youtube ")
            elif "play " in normalized and " on youtube" in normalized:
                query = normalized.split("play ")[1].split(" on youtube")[0].strip()
            elif "search " in normalized and " on youtube" in normalized:
                query = normalized.split("search ")[1].split(" on youtube")[0].strip()
            elif " on youtube" in normalized:
                parts = normalized.split(" on youtube")
                if parts[0]:
                    query = parts[0].strip()
            elif "search" in normalized:
                query = self._extract_parameter(normalized, "search youtube")
            
            if query:
                return await asyncio.to_thread(open_youtube, query)
            return await asyncio.to_thread(open_youtube)

        if self.no_llm_mode:
            return await self._route_without_llm(text, normalized)

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

        # ----------------------------------------------------------------
        # GATE 1.5: MEMORY RECORDER LAYER
        # ----------------------------------------------------------------
        memory_prefixes = [
            "remember that ",
            "remember ",
            "i prefer ",
            "i remember that ",
            "i remember ",
            "save preference ",
            "store preference "
        ]
        matched_prefix = None
        for prefix in memory_prefixes:
            if normalized.startswith(prefix):
                matched_prefix = prefix
                break

        if matched_prefix:
            if self.memory_engine:
                raw_pref = text[len(matched_prefix):].strip()
                
                # Deduce key and value, e.g. "my preference is dark mode" -> key="my preference", value="dark mode"
                if " is " in raw_pref.lower():
                    parts = raw_pref.split(" is ", 1)
                    key_part = parts[0].strip()
                    val_part = parts[1].strip()
                else:
                    key_part = "preference"
                    val_part = raw_pref
                
                self.memory_engine.learn_fact("preference", key_part.lower(), val_part)
                return f"I have committed that to memory: {raw_pref}"

        # ----------------------------------------------------------------
        # GATE 3: COGNITIVE LAYER (Context Injection & LLM Escalation)
        # ----------------------------------------------------------------
        system_state = await self.activity_tracker.get_active_window()
        rich_state = await self.context_monitor.get_context()
        context_prefix = (
            f"[System Context: Active App='{system_state['active_app']}', "
            f"Window Title='{system_state['title']}', "
            f"Workspace='{system_state['workspace_name']}', "
            f"Clipboard='{rich_state.get('clipboard', '')}']"
        )
        
        # Inject memory context if available
        memory_str = ""
        if self.memory_engine:
            try:
                mem_context = self.memory_engine.build_context(text)
                facts = mem_context.get("semantic", [])
                episodes = mem_context.get("episodic", [])
                if facts or episodes:
                    memory_str = " [Retrieved Memories: "
                    if facts:
                        memory_str += "Facts=" + "; ".join([f"{f['key']}={f['value']}" for f in facts])
                    if episodes:
                        memory_str += " Recent=" + "; ".join([f['event'] for f in episodes])
                    memory_str += "]"
            except Exception as e:
                logger.error(f"Failed to query memory: {e}")

        contextual_query = f"{context_prefix}{memory_str} {text}"

        # Route to reasoning agent with tool calling!
        if self.reasoning_agent:
            try:
                logger.info(f"Using reasoning agent for request with system state context: {context_prefix}")
                return await self.reasoning_agent.reason_and_act(contextual_query)
            except Exception as e:
                logger.error(f"Reasoning agent failed: {e}")
                return await self.llm.ask(contextual_query)
        
        # Fallback to pure LLM if reasoning agent is not loaded
        return await self.llm.ask(contextual_query)

    async def _route_without_llm(self, text: str, normalized: str) -> str:
        memory_prefixes = [
            "remember that ",
            "remember ",
            "i prefer ",
            "i remember that ",
            "i remember ",
            "save preference ",
            "store preference "
        ]
        matched_prefix = None
        for prefix in memory_prefixes:
            if normalized.startswith(prefix):
                matched_prefix = prefix
                break

        if matched_prefix and self.memory_engine:
            raw_pref = text[len(matched_prefix):].strip()
            if " is " in raw_pref.lower():
                parts = raw_pref.split(" is ", 1)
                key_part = parts[0].strip()
                val_part = parts[1].strip()
            else:
                key_part = "preference"
                val_part = raw_pref
            self.memory_engine.learn_fact("preference", key_part.lower(), val_part)
            return f"I have committed that to memory: {raw_pref}"

        if self.memory_engine and normalized.startswith(("what ", "what's ", "whats ", "who ", "where ", "when ", "how ", "why ")):
            if normalized.startswith("what"):
                return self.memory_engine.answer_what_question(text)
            if normalized.startswith("when"):
                return self.memory_engine.answer_when_question(text)
            if normalized.startswith("how"):
                return self.memory_engine.answer_how_question(text)
            if normalized.startswith("who") or normalized.startswith("where") or normalized.startswith("why"):
                return self.memory_engine.answer_what_question(text)

        if "battery" in normalized or "cpu" in normalized or "memory" in normalized or "system report" in normalized:
            raw = await asyncio.to_thread(get_system_report)
            return self._summarize_system_report(raw)

        if "list home files" in normalized or "show home files" in normalized:
            raw = await asyncio.to_thread(list_home)
            return self._summarize_file_list(raw)

        if "search file" in normalized or "find file" in normalized:
            query = self._extract_parameter(normalized, "search file") or self._extract_parameter(normalized, "find file")
            raw = await asyncio.to_thread(search_files, query)
            return self._summarize_search_results(raw)

        if "create folder" in normalized or "make folder" in normalized:
            target = self._extract_parameter(normalized, "create folder") or self._extract_parameter(normalized, "make folder")
            raw = await asyncio.to_thread(create_folder, target)
            return raw

        if "move file" in normalized and " to " in normalized:
            source, target = normalized.split(" to ", 1)
            source = source.replace("move file", "", 1).strip()
            target = target.strip()
            return await asyncio.to_thread(move_file, source, target)

        if "delete" in normalized or "remove" in normalized:
            target = self._extract_parameter(normalized, "delete") or self._extract_parameter(normalized, "remove")
            return await asyncio.to_thread(delete_path, target)

        if "close" in normalized or "kill" in normalized:
            target = self._extract_parameter(normalized, "close") or self._extract_parameter(normalized, "kill")
            return await asyncio.to_thread(kill_process, target)

        if self.memory_engine:
            suggestion = self.memory_engine.suggest_action(text)
            if suggestion:
                return suggestion

        return (
            "I am running in pure no-LLM mode. "
            "I can handle system controls, file helpers, and remembered preferences without calling a model. "
            "Try asking something like 'open Firefox', 'show battery status', or 'remember my preference is dark theme'."
        )

    def _summarize_system_report(self, report: str) -> str:
        lines = [line.strip() for line in report.splitlines() if line.strip()]
        summary = []
        for line in lines:
            if line.startswith("CPU usage") or line.startswith("Memory usage") or line.startswith("Battery") or line.startswith("Network"):
                summary.append(line)
        if not summary:
            return "I could not summarize the system report right now."
        return " | ".join(summary)

    def _summarize_file_list(self, raw: str) -> str:
        paths = [line for line in raw.splitlines() if line.strip()]
        count = len(paths)
        if count == 0:
            return "No files found in your home directory."
        sample = paths[:10]
        return f"I found {count} files in your home folder. Here are the first few: {', '.join(sample)}."

    def _summarize_search_results(self, raw: str) -> str:
        paths = [line for line in raw.splitlines() if line.strip()]
        if not paths:
            return raw
        sample = paths[:10]
        return f"Found {len(paths)} matching files. First results: {', '.join(sample)}."

    def _summarize_process_list(self, raw: str) -> str:
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        if not lines:
            return "No processes were returned."
        top = lines[:5]
        return f"Current processes: {', '.join(top)}."

    def _extract_parameter(self, text: str, phrase: str) -> str:
        if phrase not in text:
            return ""
        return text.split(phrase, 1)[1].strip()
