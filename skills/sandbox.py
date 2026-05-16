"""Sandbox for isolated skill execution."""
from typing import Any, Dict, Optional
from loguru import logger


class SkillSandbox:
    """Provides isolated execution environment for skills."""

    def __init__(self, allowed_modules: Optional[list] = None):
        """
        Initialize sandbox.

        Args:
            allowed_modules: List of allowed module names
        """
        self.allowed_modules = allowed_modules or [
            "os",
            "sys",
            "subprocess",
            "asyncio",
            "json",
            "re",
            "pathlib",
        ]
        self.execution_count = 0
        self.blocked_operations = []

    def _create_safe_env(self) -> Dict[str, Any]:
        """Create a safe execution environment."""
        import builtins

        # Create restricted builtins
        safe_builtins = {
            "__builtins__": {
                "len": len,
                "range": range,
                "str": str,
                "int": int,
                "list": list,
                "dict": dict,
                "print": print,
                "enumerate": enumerate,
                "zip": zip,
            },
        }

        return safe_builtins

    def validate_command(self, command: str) -> bool:
        """
        Validate skill command before execution.

        Args:
            command: Command string

        Returns:
            True if command is safe
        """
        dangerous_patterns = [
            "eval",
            "exec",
            "__import__",
            "open",
            "os.system",
            "subprocess.run",
            "rm -rf",
            "dd if=/dev",
        ]

        for pattern in dangerous_patterns:
            if pattern.lower() in command.lower():
                logger.warning(f"Blocked dangerous command: {pattern}")
                self.blocked_operations.append(command)
                return False

        return True

    def validate_args(self, args: Dict[str, Any]) -> bool:
        """
        Validate skill arguments.

        Args:
            args: Arguments dictionary

        Returns:
            True if arguments are safe
        """
        for key, value in args.items():
            # Check for suspicious patterns in values
            if isinstance(value, str):
                if any(
                    pattern in value
                    for pattern in ["__", "eval", "exec", "subprocess"]
                ):
                    logger.warning(f"Suspicious argument: {key}={value}")
                    return False

        return True

    def allow_module(self, module_name: str) -> None:
        """Whitelist a module."""
        if module_name not in self.allowed_modules:
            self.allowed_modules.append(module_name)
            logger.info(f"Whitelisted module: {module_name}")

    def block_module(self, module_name: str) -> None:
        """Block a module."""
        if module_name in self.allowed_modules:
            self.allowed_modules.remove(module_name)
            logger.info(f"Blocked module: {module_name}")

    def get_statistics(self) -> dict:
        """Get sandbox statistics."""
        return {
            "executions": self.execution_count,
            "blocked_operations": len(self.blocked_operations),
            "allowed_modules": self.allowed_modules,
            "blocked_operations_list": self.blocked_operations[-10:],  # Last 10
        }

    def reset_statistics(self) -> None:
        """Reset statistics."""
        self.execution_count = 0
        self.blocked_operations.clear()
        logger.info("Sandbox statistics reset")
