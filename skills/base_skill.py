from typing import Any


class BaseSkill:
    """Base class for all skills.

    Skills should implement `commands` (list of trigger phrases) and
    `execute(query, context)` as an async method.
    """

    name = "base"
    commands = []

    async def execute(self, query: str, context: dict) -> Any:
        raise NotImplementedError()
