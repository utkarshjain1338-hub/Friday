"""
Reflection Engine
Provides self-checking, retry, and clarification behavior for failed actions.
"""

from typing import List, Dict, Any
from loguru import logger


class ReflectionEngine:
    """Engine that reflects on tool execution outcomes."""

    def __init__(self, max_retries: int = 1):
        self.max_retries = max_retries
        self.retry_count = 0
        logger.info("Reflection engine initialized with max_retries=%s", max_retries)

    def analyze_results(self, user_input: str, execution_results: List[ToolExecutionResult]) -> Dict[str, Any]:
        """Analyze tool results and produce a reflection decision."""
        failed = [result for result in execution_results if not result.success]
        if not failed:
            return {"action": "none", "message": "All tools executed successfully."}

        failure = failed[0]
        error = failure.error or "Unknown error"

        # If tool call failed due to validation, ask user to correct input
        if "Missing required parameters" in error or "Invalid type" in error:
            return {
                "action": "clarify",
                "message": (
                    f"I could not use the tool {failure.tool_name} because the parameters were invalid: {error}. "
                    "Please rephrase your request or provide any missing details."
                ),
            }

        # If the tool itself failed and we have retry budget, retry once
        if self.retry_count < self.max_retries:
            self.retry_count += 1
            return {
                "action": "retry",
                "message": (
                    f"The action {failure.tool_name} failed with error: {error}. "
                    "I'll try to correct the approach and attempt it again."
                ),
                "retry_prompt": self._build_retry_prompt(user_input, execution_results),
            }

        # Otherwise, ask the user for clarification
        return {
            "action": "clarify",
            "message": (
                f"I was unable to complete the task because {failure.tool_name} failed: {error}. "
                "Could you clarify what you want me to do next?"
            ),
        }

    def _build_retry_prompt(self, user_input: str, execution_results: List[ToolExecutionResult]) -> str:
        """Build a prompt for the LLM to retry with failure context."""
        details = "\n".join(
            f"- {result.tool_name}: {result.error or 'success'}" for result in execution_results
        )
        return (
            f"I attempted to follow this request: {user_input}\n"
            "One of the tool calls failed. Here are the execution results:\n"
            f"{details}\n"
            "Please try again and adjust the tool selection or parameters so the task can succeed."
        )

    def reset(self):
        """Reset the retry counter."""
        self.retry_count = 0

    def get_status(self) -> Dict[str, Any]:
        """Return the reflection engine status."""
        return {
            "max_retries": self.max_retries,
            "retry_count": self.retry_count,
        }
