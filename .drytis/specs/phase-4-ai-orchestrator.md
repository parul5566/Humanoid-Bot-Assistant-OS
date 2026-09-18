# Phase 4 — AI Orchestrator & Task Planner

## Goal
Provider abstraction, intent understanding, structured tool-call planning, multi-step task planner, memory.

## Files
- `humanoid_bot/ai/providers/` — `base.py` (abstract chat + tool-call interface), `openai_provider.py`, `gemini_provider.py`, `ollama_provider.py`, `fake_provider.py` (scripted responses for tests)
- `humanoid_bot/ai/prompts.py` — system prompt with tool catalog + safety rules
- `humanoid_bot/ai/orchestrator.py` — conversation loop: user text → LLM → tool calls (validated JSON) → execute via tool registry → results back → final answer; NEVER executes raw shell/python
- `humanoid_bot/ai/planner.py` — decomposes multi-step requests ("prepare my workspace") into ordered structured tool calls, executes stepwise with progress reporting
- `humanoid_bot/ai/memory.py` — short-term conversation buffer, task history, optional long-term memory (consent-gated, viewable/clearable)
- Tool registry: `humanoid_bot/tools/registry.py` — each tool has typed pydantic argument schema, risk level, description

## Acceptance Criteria
- [ ] Chat conversation works end-to-end via at least the OpenAI-compatible provider and the fake provider
- [ ] A request like "open notepad" produces a structured tool call `{tool, arguments}` — never a shell command
- [ ] Multi-step request produces ordered steps with progress shown in UI ("Step 2 of 5…")
- [ ] Invalid tool arguments are rejected with a user-visible apology, not a crash
- [ ] Switching provider in settings works without code changes
- [ ] Memory settings allow view/clear of stored conversation data
