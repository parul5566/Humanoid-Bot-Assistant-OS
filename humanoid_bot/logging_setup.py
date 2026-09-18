"""Structured logging with a redaction filter.

Never log: API keys, passwords, tokens, clipboard contents.
"""

from __future__ import annotations

import logging
import re
import sys
from collections.abc import Iterable

from humanoid_bot.app.paths import log_dir

REDACTED = "[REDACTED]"

_DEFAULT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(api[_-]?key|token|secret|password|authorization)\s*[=:].*$"),
    re.compile(r"\bsk-[A-Za-z0-9]{16,}\b"),
    re.compile(r"\bBearer\s+\S+", re.IGNORECASE),
)


class RedactionFilter(logging.Filter):
    """Mask anything that looks like a credential in log records."""

    def __init__(self, extra_patterns: Iterable[re.Pattern[str]] = ()) -> None:
        super().__init__()
        self.patterns = (*_DEFAULT_PATTERNS, *extra_patterns)

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for pattern in self.patterns:
            message = pattern.sub(REDACTED, message)
        record.msg = message
        record.args = ()
        return True


def setup_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    root.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    handler.addFilter(RedactionFilter())
    root.handlers.clear()
    root.addHandler(handler)

    file_handler = logging.FileHandler(log_dir() / "app.log", encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    file_handler.addFilter(RedactionFilter())
    root.addHandler(file_handler)
