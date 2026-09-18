"""LLM provider abstraction.

Every provider exposes a single chat interface that accepts messages and a
tool catalog and returns either text or structured tool calls. Providers are
OpenAI-compatible by contract: gemini/ollama adapters translate to that wire
format. A FakeProvider enables deterministic tests without network.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

Role = Literal["system", "user", "assistant", "tool"]


@dataclass
class Message:
    role: Role
    content: str
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolSpec:
    """A tool description handed to the LLM (name/args/description only)."""

    name: str
    description: str
    parameters_schema: dict[str, Any]


@dataclass
class ChatResult:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


class LLMProvider(Protocol):
    name: str

    def chat(
        self,
        messages: list[Message],
        tools: list[ToolSpec],
        temperature: float = 0.3,
    ) -> ChatResult: ...


# --------------------------------------------------------------------------
def _encode_tools(tools: list[ToolSpec]) -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters_schema,
            },
        }
        for tool in tools
    ]


class OpenAICompatibleProvider:
    """Works with OpenAI and any compatible gateway (base_url override)."""

    name = "openai"

    def __init__(self, model: str, api_key_env: str, base_url: str | None = None) -> None:
        self.model = model
        self.api_key_env = api_key_env
        self.base_url = base_url

    def chat(
        self,
        messages: list[Message],
        tools: list[ToolSpec],
        temperature: float = 0.3,
    ) -> ChatResult:
        import httpx

        api_key = os.environ.get(self.api_key_env)
        if not api_key:
            raise RuntimeError(f"Set {self.api_key_env} to use the {self.name} provider")
        base = self.base_url or "https://api.openai.com/v1"
        payload_messages: list[dict[str, Any]] = []
        for msg in messages:
            entry: dict[str, Any] = {"role": msg.role, "content": msg.content}
            if msg.tool_calls:
                entry["tool_calls"] = [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.name,
                            "arguments": json.dumps(call.arguments),
                        },
                    }
                    for call in msg.tool_calls
                ]
            if msg.tool_call_id:
                entry["tool_call_id"] = msg.tool_call_id
            payload_messages.append(entry)

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": payload_messages,
            "temperature": temperature,
        }
        if tools:
            payload["tools"] = _encode_tools(tools)

        response = httpx.post(
            f"{base.rstrip('/')}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        choice = data["choices"][0]["message"]
        result = ChatResult(text=choice.get("content") or "")
        for raw in choice.get("tool_calls") or []:
            result.tool_calls.append(
                ToolCall(
                    id=raw["id"],
                    name=raw["function"]["name"],
                    arguments=json.loads(raw["function"]["arguments"] or "{}"),
                )
            )
        return result


class OllamaProvider(OpenAICompatibleProvider):
    """Ollama exposes an OpenAI-compatible endpoint at /v1."""

    name = "ollama"

    def __init__(self, model: str) -> None:
        super().__init__(
            model=model,
            api_key_env="HUMANOID_BOT_OLLAMA_NO_KEY",
            base_url=os.environ.get("HUMANOID_BOT_OLLAMA_URL", "http://localhost:11434/v1"),
        )


class GeminiProvider(OpenAICompatibleProvider):
    """Gemini offers an OpenAI-compatible endpoint."""

    name = "gemini"

    def __init__(self, model: str) -> None:
        super().__init__(
            model=model,
            api_key_env="HUMANOID_BOT_GEMINI_API_KEY",
            base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        )


class FakeProvider:
    """Scripted responses for deterministic tests: one ChatResult per call."""

    name = "fake"

    def __init__(self, script: list[ChatResult] | None = None) -> None:
        self.script = script or []
        self.calls: list[list[Message]] = []
        self._index = 0

    def chat(
        self,
        messages: list[Message],
        tools: list[ToolSpec],
        temperature: float = 0.3,
    ) -> ChatResult:
        self.calls.append(list(messages))
        if not self.script:
            return ChatResult(text="OK.")
        result = self.script[self._index % len(self.script)]
        self._index += 1
        return result


def create_provider(provider: str, model: str, **kwargs: str) -> LLMProvider:
    if provider == "fake":
        return FakeProvider()
    if provider == "openai":
        return OpenAICompatibleProvider(
            model=model,
            api_key_env=kwargs.get("api_key_env", "HUMANOID_BOT_API_KEY"),
            base_url=kwargs.get("base_url") or None,
        )
    if provider == "ollama":
        return OllamaProvider(model=model)
    if provider == "gemini":
        return GeminiProvider(model=model)
    raise ValueError(f"Unknown provider: {provider}")
