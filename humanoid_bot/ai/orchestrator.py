"""AI orchestrator: conversation loop with structured tool calling.

Flow: user text -> LLM -> tool calls (validated) -> registry.execute (with
permission/confirmation/audit) -> results back to LLM -> final answer.
The LLM never runs code or shell directly.
"""

from __future__ import annotations

import json
from collections.abc import Callable

from humanoid_bot.ai.memory import Memory
from humanoid_bot.ai.prompts import SYSTEM_PROMPT
from humanoid_bot.ai.providers.base import (
    ChatResult,
    LLMProvider,
    Message,
    ToolSpec,
)
from humanoid_bot.tools.registry import ToolRegistry


class Orchestrator:
    def __init__(
        self,
        provider: LLMProvider,
        registry: ToolRegistry,
        memory: Memory,
        temperature: float = 0.3,
        max_context_messages: int = 20,
        max_tool_rounds: int = 6,
        on_step: Callable[[str], None] | None = None,
    ) -> None:
        self.provider = provider
        self.registry = registry
        self.memory = memory
        self.temperature = temperature
        self.max_context_messages = max_context_messages
        self.max_tool_rounds = max_tool_rounds
        self.on_step = on_step or (lambda _s: None)

    # ------------------------------------------------------------------
    def _build_messages(self, user_text: str) -> list[Message]:
        messages: list[Message] = [Message(role="system", content=SYSTEM_PROMPT)]
        for role, content in self.memory.conversation(self.max_context_messages):
            messages.append(Message(role=role, content=content))  # type: ignore[arg-type]
        messages.append(Message(role="user", content=user_text))
        return messages

    def handle_user_text(self, user_text: str) -> str:
        """Process one user request end-to-end; returns the assistant reply."""
        self.memory.remember_turn("user", user_text)
        messages = self._build_messages(user_text)

        for _round in range(self.max_tool_rounds):
            result: ChatResult = self.provider.chat(
                messages, self._provider_tools(), self.temperature
            )
            if not result.tool_calls:
                self.memory.remember_turn("assistant", result.text)
                return result.text

            assistant_msg = Message(
                role="assistant",
                content=result.text,
                tool_calls=result.tool_calls,
            )
            messages.append(assistant_msg)

            for call in result.tool_calls:
                self.on_step(f"Running {call.name}...")
                outcome = self.registry.execute(call.name, call.arguments)
                messages.append(
                    Message(
                        role="tool",
                        content=json.dumps(outcome),
                        tool_call_id=call.id,
                    )
                )

        self.memory.remember_turn(
            "assistant", "I stopped after too many tool steps - please rephrase."
        )
        return "I stopped after too many tool steps - please rephrase."

    # ------------------------------------------------------------------
    def _provider_tools(self) -> list[ToolSpec]:
        # Providers take a simplified ToolSpec list; we reuse registry specs.
        from humanoid_bot.ai.providers.base import ToolSpec

        specs: list[ToolSpec] = []
        for raw in self.registry.tool_specs():
            function = raw["function"]
            assert isinstance(function, dict)
            specs.append(
                ToolSpec(
                    name=str(function["name"]),
                    description=str(function["description"]),
                    parameters_schema=function.get("parameters", {}),
                )
            )
        return specs


