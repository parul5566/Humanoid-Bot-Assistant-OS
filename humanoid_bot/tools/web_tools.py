"""Web assistant tool: search vs open-URL vs read-page."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, cast

import httpx
from pydantic import BaseModel, Field

from humanoid_bot.tools.results import ToolResult

if TYPE_CHECKING:
    from humanoid_bot.tools.registry import ToolRegistry

SEARCH_URL = "https://duckduckgo.com/html/?q="


class WebSearchArgs(BaseModel):
    query: str = Field(min_length=1, max_length=300)


class OpenUrlArgs(BaseModel):
    url: str = Field(min_length=1)


class ReadPageArgs(BaseModel):
    url: str
    max_chars: int = Field(default=4000, ge=200, le=20000)


def register_web_tools(
    registry: ToolRegistry,
    open_in_browser: Callable[[str], None] | None = None
) -> None:
    from humanoid_bot.tools.registry import Risk, ToolDefinition

    opener = open_in_browser
    if opener is None:
        def opener_default(url: str) -> None:
            import webbrowser

            webbrowser.open(url)
        opener = opener_default

    def web_search(args_b: BaseModel) -> ToolResult:
        args = cast(WebSearchArgs, args_b)
        try:
            response = httpx.get(
                SEARCH_URL + args.query.replace(" ", "+"),
                headers={"User-Agent": "Mozilla/5.0 HumanoidBot"},
                timeout=20,
                follow_redirects=True,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            return {"ok": False, "summary": f"Web search failed: {exc}"}
        results = _extract_results(response.text)
        if not results:
            return {"ok": True, "summary": "No results found."}
        listing = "\n".join(f"- {title}: {url}" for title, url in results[:5])
        return {"ok": True, "summary": f"Top results for '{args.query}':", "detail": listing}

    def open_url(args_b: BaseModel) -> ToolResult:
        args = cast(OpenUrlArgs, args_b)
        if not args.url.startswith(("http://", "https://")):
            return {"ok": False, "summary": "URL must start with http:// or https://"}
        opener(args.url)
        return {"ok": True, "summary": f"Opened {args.url} in the browser."}

    def read_page(args_b: BaseModel) -> ToolResult:
        args = cast(ReadPageArgs, args_b)
        try:
            response = httpx.get(
                args.url,
                headers={"User-Agent": "Mozilla/5.0 HumanoidBot"},
                timeout=20,
                follow_redirects=True,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            return {"ok": False, "summary": f"Couldn't read the page: {exc}"}
        text = _html_to_text(response.text)
        return {"ok": True, "summary": text[: args.max_chars]}


    definitions: tuple[ToolDefinition[BaseModel], ...] = (
        ToolDefinition("web_search", "Search the web for a query",
                       WebSearchArgs, web_search, Risk.LOW),
        ToolDefinition("open_url", "Open a URL in the default browser",
                       OpenUrlArgs, open_url, Risk.LOW),
        ToolDefinition("read_page", "Read the visible text of a webpage",
                       ReadPageArgs, read_page, Risk.LOW),
    )
    for definition in definitions:
        registry.register(definition)


def _extract_results(html: str) -> list[tuple[str, str]]:
    import re

    pattern = re.compile(
        r"<a[^>]+class=\"result__a\"[^>]+href=\"([^\"]+)\"[^>]*>(.*?)</a>", re.S
    )
    out: list[tuple[str, str]] = []
    for url, title in pattern.findall(html):
        clean = re.sub(r"<[^>]+>", "", title).strip()
        out.append((clean, url))
    return out


def _html_to_text(html: str) -> str:
    import re

    html = re.sub(r"<(script|style).*?</\1>", "", html, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
