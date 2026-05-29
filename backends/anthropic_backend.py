import anthropic
from fastapi import HTTPException

from utils.config import settings


def _map_error(exc: anthropic.APIError) -> HTTPException:
    if isinstance(exc, anthropic.AuthenticationError):
        return HTTPException(401, "Invalid Anthropic API key. Check ANTHROPIC_API_KEY in .env.")
    if isinstance(exc, anthropic.RateLimitError):
        return HTTPException(429, "Anthropic rate limit reached. Please wait and retry.")
    if isinstance(exc, anthropic.APIConnectionError):
        return HTTPException(503, "Could not reach the Claude API. Check your network.")
    if isinstance(exc, anthropic.BadRequestError):
        return HTTPException(400, f"Claude rejected the request: {exc.message}")
    return HTTPException(502, f"Claude API error ({exc.status_code}).")


class AnthropicBackend:
    name = "anthropic"
    _model = "claude-sonnet-4-6"

    def __init__(self) -> None:
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.async_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    def _kwargs(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict] | None,
        tool_name: str | None,
        cache_system: bool,
        max_tokens: int,
    ) -> dict:
        system_block: dict = {"type": "text", "text": system}
        if cache_system:
            system_block["cache_control"] = {"type": "ephemeral"}
        kw: dict = dict(
            model=self._model,
            max_tokens=max_tokens,
            system=[system_block],
            messages=messages,
        )
        if tools:
            kw["tools"] = tools
            kw["tool_choice"] = (
                {"type": "tool", "name": tool_name} if tool_name else {"type": "any"}
            )
        return kw

    def _extract(self, response: anthropic.types.Message) -> dict:
        for block in response.content:
            if block.type == "tool_use":
                return block.input  # type: ignore[return-value]
        raise ValueError("No tool_use block in Anthropic response.")

    def complete(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_name: str | None = None,
        cache_system: bool = False,
        max_tokens: int = 2048,
    ) -> dict:
        try:
            return self._extract(
                self.client.messages.create(
                    **self._kwargs(system, messages, tools, tool_name, cache_system, max_tokens)
                )
            )
        except anthropic.APIError as exc:
            raise _map_error(exc) from exc

    async def acomplete(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_name: str | None = None,
        cache_system: bool = False,
        max_tokens: int = 2048,
    ) -> dict:
        try:
            return self._extract(
                await self.async_client.messages.create(
                    **self._kwargs(system, messages, tools, tool_name, cache_system, max_tokens)
                )
            )
        except anthropic.APIError as exc:
            raise _map_error(exc) from exc
