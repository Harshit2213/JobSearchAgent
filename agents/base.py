from backends.router import get_router


class BaseAgent:
    _quality: str = "high"  # subclasses override to "fast" for Groq routing

    def _call(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_name: str | None = None,
        cache_system: bool = False,
        max_tokens: int = 2048,
    ) -> dict:
        return get_router().complete(
            quality=self._quality,
            system=system,
            messages=messages,
            tools=tools,
            tool_name=tool_name,
            cache_system=cache_system,
            max_tokens=max_tokens,
        )

    async def _acall(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_name: str | None = None,
        cache_system: bool = False,
        max_tokens: int = 2048,
    ) -> dict:
        return await get_router().acomplete(
            quality=self._quality,
            system=system,
            messages=messages,
            tools=tools,
            tool_name=tool_name,
            cache_system=cache_system,
            max_tokens=max_tokens,
        )

    def _extract_tool_input(self, response: dict) -> dict:
        # Backends now return the extracted tool-input dict directly.
        # This pass-through keeps all existing agent call sites unchanged.
        return response
