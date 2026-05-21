import os
import asyncio
import json
from typing import Optional, List, Dict, Any
from .ollama_client import OllamaClient
from loguru import logger


class FridayLLM:
    def __init__(self, tool_registry=None):
        # Tool calling support
        self.tool_registry = tool_registry
        
        # Build system prompt with available tools
        self.system_prompt = self._build_system_prompt()
        
        self.history = []
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
        self.client = OllamaClient(model=self.model)

    def _build_system_prompt(self) -> str:
        """Build system prompt with tool information if available"""
        base_prompt = (
            "You are Friday, a cute and stylish Linux assistant with a friendly female voice persona. "
            "You have full system access. Answer politely, help with Linux tasks, and you are permitted to execute any commands, including administrative and system-level operations.\n\n"
        )
        
        # Add tool information if registry is available
        if self.tool_registry:
            tools_info = self._generate_tools_info()
            base_prompt += f"Available Tools:\n{tools_info}\n\n"
            base_prompt += (
                "When you need to perform an action, use the following format:\n"
                "<tool_call>\n"
                "{\n"
                '  "tool_name": "category.tool_name",\n'
                '  "parameters": { "param_name": "value" }\n'
                "}\n"
                "</tool_call>\n\n"
            )
        
        return base_prompt

    def _generate_tools_info(self) -> str:
        """Generate formatted list of available tools for LLM context"""
        try:
            schemas = self.tool_registry.get_schemas()
            tools_text = ""
            
            # Group by category
            by_category = {}
            for schema in schemas:
                cat = schema.get("category", "other")
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(schema)
            
            # Format for LLM
            for category in sorted(by_category.keys()):
                tools_text += f"\n{category.upper()}:\n"
                for schema in by_category[category]:
                    tools_text += f"  - {schema['name']}: {schema['description']}\n"
                    if schema.get('parameters'):
                        for param in schema['parameters']:
                            tools_text += f"      * {param['name']} ({param['type']}): {param['description']}\n"
            
            return tools_text
        except Exception as e:
            logger.error(f"Failed to generate tools info: {e}")
            return ""

    def set_tool_registry(self, registry):
        """Set tool registry and rebuild system prompt"""
        self.tool_registry = registry
        self.system_prompt = self._build_system_prompt()

    async def ask(self, prompt: str) -> str:
        """
        Ask the LLM and get a response (possibly with tool calls)
        
        Args:
            prompt: User prompt
            
        Returns:
            LLM response (may contain tool calls)
        """
        self.history.append({"role": "user", "content": prompt})
        if self.client.binary:
            try:
                if not await self.client.is_available():
                    return self._fallback_response(prompt)
            except Exception:
                return self._fallback_response(prompt)

        if not self.client.binary:
            return self._fallback_response(prompt)

        try:
            response = await self.client.generate(prompt, history=self.history, system=self.system_prompt)
            self.history.append({"role": "assistant", "content": response})
            return response
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return self._fallback_response(prompt)

    async def ask_with_tool_context(self, prompt: str, tool_results: Optional[List[Dict]] = None) -> str:
        """
        Ask with tool execution context
        
        Args:
            prompt: User prompt
            tool_results: Results from previous tool calls to include in context
            
        Returns:
            LLM response
        """
        # Add tool results to history if provided
        if tool_results:
            context = "Tool execution results:\n"
            for result in tool_results:
                context += f"- {result.get('tool_name')}: {result.get('result')}\n"
            
            full_prompt = f"{prompt}\n\n{context}"
        else:
            full_prompt = prompt
        
        return await self.ask(full_prompt)

    def _fallback_response(self, prompt: str) -> str:
        if "thank" in prompt.lower():
            return "You're welcome! If you want, I can also run commands or check system status."
        if "help" in prompt.lower() or "how" in prompt.lower() or "what" in prompt.lower():
            return (
                "Friday can open apps, check system stats, manage files, and perform full system automation. "
                "Try commands like 'open firefox', 'show battery status', or 'search file notes'."
            )
        return (
            "Friday here! I can help with Linux tasks and full system automation. "
            "Ask me to open an application, inspect system health, or find files."
        )
