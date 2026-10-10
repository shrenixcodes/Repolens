"""Logging configuration with secret redaction.

RepoLens logs should never contain API keys/tokens or full source-file
bodies. This module centralizes logger setup so every entry point (CLI, API,
background jobs) gets the same redaction behavior instead of each one
remembering to apply it.
"""

from __future__ import annotations

import logging
import re
import sys
from typing import IO

# Matches common secret-shaped substrings: "api_key=...", "token: ...",
# bearer tokens, and OpenAI-style "sk-..." keys. Intentionally broad --
# false positives (redacting something that wasn't actually a secret) are
# an acceptable cost, false negatives are not.
_SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)([^\s'\"]+)"),
    re.compile(r"(?i)(authorization:\s*bearer\s+)([^\s'\"]+)"),
    re.compile(r"(?i)(token\s*[=:]\s*)([^\s'\"]+)"),
    re.compile(r"(?i)(secret\s*[=:]\s*)([^\s'\"]+)"),
    re.compile(r"sk-[A-Za-z0-9]{10,}"),
]


def redact(message: str) -> str:
    """Redact anything in ``message`` that looks like a credential."""
    redacted = message
    for pattern in _SECRET_PATTERNS:
        if pattern.groups >= 2:
            redacted = pattern.sub(r"\1[REDACTED]", redacted)
        else:
            redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


class RedactingFilter(logging.Filter):
    """A logging filter that redacts secret-shaped substrings from records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact(record.msg)
        if record.args:
            record.args = tuple(
                redact(arg) if isinstance(arg, str) else arg for arg in record.args
            )
        return True


def configure_logging(level: int = logging.INFO, *, stream: IO[str] | None = None) -> None:
    """Configure root logging with redaction applied to every handler.

    Idempotent: safe to call multiple times (e.g. once per CLI invocation)
    without stacking duplicate handlers.
    """
    root = logging.getLogger()
    root.setLevel(level)

    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    handler.addFilter(RedactingFilter())
    root.addHandler(handler)
