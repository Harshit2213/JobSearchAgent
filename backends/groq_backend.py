import json

import openai
from fastapi import HTTPException

from utils.config import settings

_GROQ_BASE_URL = "https://api.groq.com/openai/v1"


def _map_error(exc: openai.APIError) -> None:
    if isinstance(exc, openai.AuthenticationError):
        raise HTTPException(401, "Invalid Groq API key. Check GROQ_API_KEY in .env.")
    if isinstance(exc, openai.RateLimitError):
        raise HTTPException(429, "Groq rate limit reached. Please wait and retry.")
    if isinstance(exc, openai.APIConnectionError):
        raise HTTPException(503, "Could not reach the Groq API. Check your network.")
    raise HTTPException(502, f"Groq API error: {exc}")


class GroqBackend:
    name = "groq"

    def __init__(self) -> None:
        self._sync  = openai.OpenAI(
            api_key=settings.groq_api_key, base_url=_GROQ_BASE_URL
        )
        self._async = openai.AsyncOpenAI(
            api_key=settings.groq_api_key, base_url=_GROQ_BASE_URL
        )

    # ── tool format adapter ────────────────────────────────────────────────────
    # Anthropic uses `input_schema`; OpenAI/Groq uses `function.parameters`

    @staticmethod
    def _adapt_tools(tools: list[dict]) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t["input_schema"],
                },
            }
            for t in tools
        ]

    @staticmethod
    def _adapt_tool_choice(tool_name: str | None):
        if tool_name:
            return {"type": "function", "function": {"name": tool_name}}
        return "required"

    @staticmethod
    def _extract(response) -> dict:
        tool_calls = response.choices[0].message.tool_calls
        if not tool_calls:
            raise ValueError("No tool_calls in Groq response.")
        return json.loads(tool_calls[0].function.arguments)

    def _build_kwargs(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict] | None,
        tool_name: str | None,
        max_tokens: int,
    ) -> dict:
        kw: dict = dict(
            model=settings.groq_model,
            max_tokens=max_tokens,
            messages=[{"role": "system", "content": system}, *messages],
        )
        if tools:
            kw["tools"] = self._adapt_tools(tools)
            kw["tool_choice"] = self._adapt_tool_choice(tool_name)
        return kw

    # ── public interface ──────────────────────────────────────────────────────

    def complete(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_name: str | None = None,
        cache_system: bool = False,   # ignored — Groq has no prompt caching
        max_tokens: int = 2048,
    ) -> dict:
        try:
            resp = self._sync.chat.completions.create(
                **self._build_kwargs(system, messages, tools, tool_name, max_tokens)
            )
            return self._extract(resp)
        except openai.APIError as exc:
            _map_error(exc)

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
            resp = await self._async.chat.completions.create(
                **self._build_kwargs(system, messages, tools, tool_name, max_tokens)
            )
            return self._extract(resp)
        except openai.APIError as exc:
            _map_error(exc)
