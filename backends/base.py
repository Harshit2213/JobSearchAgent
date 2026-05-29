from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMBackend(Protocol):
    name: str

    def complete(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict] | None,
        tool_name: str | None,
        cache_system: bool,
        max_tokens: int,
    ) -> dict: ...

    async def acomplete(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict] | None,
        tool_name: str | None,
        cache_system: bool,
        max_tokens: int,
    ) -> dict: ...
