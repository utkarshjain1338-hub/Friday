"""
brain/reflection_engine.py
Lightweight reflection / retry logic for the ReasoningAgent.

When a tool call fails the engine analyses the results and decides
whether to retry with a rephrased prompt or give up gracefully.
"""

from typing import Any, Dict, List, Optional
from loguru import logger


class ReflectionEngine:
    """
    Analyses failed tool executions and recommends a recovery action.

    Actions returned:
      - "retry"  : rephrase the prompt and try again
      - "partial": some tools succeeded, return partial result
      - "stop"   : too many retries or unrecoverable error
    """

    def __init__(self, max_retries: int = 1):
        self.max_retries = max_retries
        self._retry_count = 0

    # ------------------------------------------------------------------

    def analyze_results(
        self,
        original_query: str,
        results: List[Any],          # List[ToolExecutionResult]
    ) -> Dict[str, Any]:
        """
        Inspect tool results and return a recovery plan.

        Returns a dict with keys:
          action  : "retry" | "partial" | "stop"
          message : human-readable explanation
          retry_prompt : (only when action=="retry") the rephrased prompt
        """
        failed  = [r for r in results if not r.success]
        success = [r for r in results if r.success]

        # Collect partial successes as a readable string
        partial_text = " ".join(str(r.result) for r in success if r.result)

        if self._retry_count >= self.max_retries:
            logger.warning(
                "ReflectionEngine: max retries (%d) reached — giving up.",
                self.max_retries,
            )
            msg = (
                partial_text
                or "I tried but could not complete the request. Please try rephrasing."
            )
            return {"action": "stop", "message": msg}

        if not failed:
            # Everything succeeded — shouldn't normally reach here
            return {
                "action": "partial",
                "message": partial_text or "Done.",
            }

        # Build a description of what went wrong
        error_summary = "; ".join(
            f"{r.tool_name}: {r.error}" for r in failed
        )
        logger.info(
            "ReflectionEngine: retrying after failures — %s", error_summary
        )

        self._retry_count += 1
        retry_prompt = (
            f"{original_query} "
            f"(Previous attempt failed: {error_summary}. "
            f"Please try a different approach.)"
        )

        return {
            "action": "retry",
            "message": f"Retrying after error: {error_summary}",
            "retry_prompt": retry_prompt,
        }

    def reset(self):
        """Reset retry counter between independent requests."""
        self._retry_count = 0
