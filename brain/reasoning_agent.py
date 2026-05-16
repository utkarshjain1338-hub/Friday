"""
Reasoning Agent
Orchestrates LLM with tool calling
"""

import re
from typing import Optional, List, Dict, Any
from loguru import logger
from .llm import FridayLLM
from .reflection_engine import ReflectionEngine
from tools.tool_orchestrator import ToolOrchestrator, ToolCall


class ReasoningAgent:
    """
    Cognitive agent that uses LLM reasoning with dynamic tool calling
    """
    
    def __init__(self, llm: FridayLLM, orchestrator: ToolOrchestrator):
        self.llm = llm
        self.orchestrator = orchestrator
        self.max_tool_iterations = 5
        self.conversation_context = []
        self.reflection_engine = ReflectionEngine(max_retries=1)
    
    async def reason_and_act(self, user_input: str) -> str:
        """
        Core reasoning loop with tool calling
        
        Args:
            user_input: User's request
            
        Returns:
            Final response to user
        """
        logger.info(f"Starting reasoning for: {user_input}")
        
        self.conversation_context.append({
            "type": "user",
            "content": user_input
        })
        
        iteration = 0
        while iteration < self.max_tool_iterations:
            iteration += 1
            logger.info(f"Reasoning iteration {iteration}")
            
            # Get LLM response
            response = await self.llm.ask(user_input)
            logger.debug(f"LLM response: {response}")
            
            # Parse tool calls from response
            tool_calls = self.orchestrator.parse_tool_calls_from_text(response)
            
            if not tool_calls:
                # No tool calls - this is the final response
                logger.info("No tool calls detected, returning final response")
                self.conversation_context.append({
                    "type": "assistant",
                    "content": response
                })
                return self._extract_text_response(response)
            
            # Execute tool calls
            logger.info(f"Executing {len(tool_calls)} tool calls")
            results = await self.orchestrator.execute_tool_sequence(tool_calls)
            
            # Build context for next iteration
            tool_results = []
            all_successful = True
            
            for result in results:
                tool_results.append(result.to_dict())
                if not result.success:
                    all_successful = False
                    logger.warning(f"Tool failed: {result.tool_name} - {result.error}")
            
            # If all tools succeeded, ask for final response
            if all_successful and tool_results:
                logger.info("All tools executed successfully, asking for final response")
                final_response = await self.llm.ask_with_tool_context(
                    user_input,
                    tool_results
                )
                
                self.conversation_context.append({
                    "type": "assistant",
                    "content": final_response
                })
                self.reflection_engine.reset()
                return self._extract_text_response(final_response)
            
            # If any tool failed, use reflection logic
            if not all_successful:
                reflection = self.reflection_engine.analyze_results(user_input, results)
                logger.warning("Reflection action: %s", reflection.get("action"))
                
                if reflection.get("action") == "retry" and reflection.get("retry_prompt"):
                    logger.info("Retrying with reflected prompt")
                    user_input = reflection.get("retry_prompt")
                    continue
                
                return reflection.get("message", "Some tools failed. Please try again or rephrase your request.")
        
        logger.warning(f"Reached max iterations ({self.max_tool_iterations})")
        return "I need more information or assistance to complete this task."

    def _extract_text_response(self, response: str) -> str:
        """
        Extract clean text response without tool calls
        
        Args:
            response: Raw LLM response
            
        Returns:
            Clean text response
        """
        # Remove tool_call blocks
        clean = re.sub(r'<tool_call>.*?</tool_call>', '', response, flags=re.DOTALL)
        # Remove extra whitespace
        clean = ' '.join(clean.split())
        return clean.strip()

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.conversation_context.copy()

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_context = []

    async def multi_turn_chat(self, user_input: str) -> str:
        """
        Multi-turn conversation with reasoning
        
        Args:
            user_input: User input for this turn
            
        Returns:
            Assistant response
        """
        return await self.reason_and_act(user_input)

    def get_tool_summary(self) -> Dict[str, Any]:
        """
        Get summary of tool usage
        
        Returns:
            Summary statistics
        """
        return self.orchestrator.get_execution_summary()
