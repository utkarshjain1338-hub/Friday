"""Skill executor for safe and isolated skill execution."""
import asyncio
from typing import Optional, Dict, Any
from loguru import logger


class SkillExecutor:
    """Executes skills with isolation and error handling."""

    def __init__(self, timeout: float = 30.0):
        """
        Initialize skill executor.

        Args:
            timeout: Skill execution timeout in seconds
        """
        self.timeout = timeout
        self.running_skills: Dict[str, asyncio.Task] = {}

    async def execute(
        self,
        skill,
        command: str,
        args: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a skill safely.

        Args:
            skill: Skill instance with execute method
            command: Command to execute
            args: Command arguments

        Returns:
            Result dictionary
        """
        skill_name = getattr(skill, "name", "unknown")
        skill_id = f"{skill_name}_{id(skill)}"

        try:
            logger.info(f"Executing skill: {skill_name} with command: {command}")

            # Check if skill has execute method
            if not hasattr(skill, "execute"):
                return {
                    "success": False,
                    "error": f"Skill {skill_name} has no execute method",
                }

            # Create execution task
            if asyncio.iscoroutinefunction(skill.execute):
                coro = skill.execute(command, args)
            else:
                # Wrap sync function in async
                coro = asyncio.to_thread(skill.execute, command, args)

            # Store running task
            task = asyncio.create_task(coro)
            self.running_skills[skill_id] = task

            try:
                # Execute with timeout
                result = await asyncio.wait_for(task, timeout=self.timeout)
                logger.info(f"Skill {skill_name} completed successfully")
                return {"success": True, "result": result}

            except asyncio.TimeoutError:
                logger.warning(f"Skill {skill_name} timeout after {self.timeout}s")
                task.cancel()
                return {"success": False, "error": f"Skill execution timeout after {self.timeout}s"}

            except asyncio.CancelledError:
                logger.info(f"Skill {skill_name} was cancelled")
                return {"success": False, "error": "Skill execution cancelled"}

        except Exception as e:
            logger.error(f"Skill {skill_name} execution error: {e}")
            return {"success": False, "error": str(e)}

        finally:
            self.running_skills.pop(skill_id, None)

    async def execute_with_fallback(
        self,
        skill,
        command: str,
        args: Dict[str, Any],
        fallback_result: Optional[str] = None,
    ) -> str:
        """
        Execute skill with fallback on failure.

        Args:
            skill: Skill instance
            command: Command
            args: Arguments
            fallback_result: Fallback result if skill fails

        Returns:
            Result or fallback
        """
        result = await self.execute(skill, command, args)

        if result["success"]:
            if isinstance(result.get("result"), str):
                return result["result"]
            else:
                return str(result.get("result", ""))
        else:
            error_msg = result.get("error", "Unknown error")
            logger.warning(f"Skill failed: {error_msg}")
            return fallback_result or f"Skill execution failed: {error_msg}"

    async def cancel_skill(self, skill_name: str) -> bool:
        """
        Cancel a running skill.

        Args:
            skill_name: Name of skill to cancel

        Returns:
            True if cancelled, False if not found
        """
        for skill_id, task in list(self.running_skills.items()):
            if skill_name in skill_id and not task.done():
                task.cancel()
                logger.info(f"Cancelled skill: {skill_name}")
                return True
        return False

    async def cancel_all(self) -> int:
        """
        Cancel all running skills.

        Returns:
            Number of skills cancelled
        """
        count = 0
        for task in list(self.running_skills.values()):
            if not task.done():
                task.cancel()
                count += 1
        logger.info(f"Cancelled {count} running skills")
        return count

    def get_running_count(self) -> int:
        """Get number of running skills."""
        return len([t for t in self.running_skills.values() if not t.done()])

    def get_running_skills(self) -> list:
        """Get list of running skill IDs."""
        return [sid for sid, t in self.running_skills.items() if not t.done()]


# Global singleton
_executor: Optional[SkillExecutor] = None


async def get_skill_executor(timeout: float = 30.0) -> SkillExecutor:
    """Get or create the global skill executor."""
    global _executor
    if _executor is None:
        _executor = SkillExecutor(timeout=timeout)
    return _executor
