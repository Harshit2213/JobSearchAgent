import anthropic

from utils.config import settings


class BaseAgent:
    _model = "claude-sonnet-4-6"

    def __init__(self) -> None:
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def _call(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_name: str | None = None,
        cache_system: bool = False,
        max_tokens: int = 2048,
    ) -> anthropic.types.Message:
        system_block: dict = {"type": "text", "text": system}
        if cache_system:
            system_block["cache_control"] = {"type": "ephemeral"}

        kwargs: dict = dict(
            model=self._model,
            max_tokens=max_tokens,
            system=[system_block],
            messages=messages,
        )
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = (
                {"type": "tool", "name": tool_name} if tool_name else {"type": "any"}
            )

        return self.client.messages.create(**kwargs)

    def _extract_tool_input(self, response: anthropic.types.Message) -> dict:
        for block in response.content:
            if block.type == "tool_use":
                return block.input  # type: ignore[return-value]
        raise ValueError("No tool_use block found in Claude response.")
