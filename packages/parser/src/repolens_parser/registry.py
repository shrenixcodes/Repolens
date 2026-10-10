"""Pluggable language-parser registry."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from repolens_parser.models import ParseResult


@runtime_checkable
class LanguageParser(Protocol):
    """A parser for one source language.

    Implementations must never raise on malformed input -- a syntax error
    in one file must not stop the rest of the repository from being
    indexed. Report the problem via ``ParseResult.errors`` instead.
    """

    language: str
    extensions: frozenset[str]

    def parse(self, path: str, source: str) -> ParseResult: ...


class ParserRegistry:
    """Maps file extensions to the parser responsible for them."""

    def __init__(self) -> None:
        self._parsers: dict[str, LanguageParser] = {}
        self._unavailable: dict[str, str] = {}

    def register(self, parser: LanguageParser) -> None:
        for ext in parser.extensions:
            self._parsers[ext] = parser

    def mark_unavailable(self, language: str, reason: str) -> None:
        """Record that a language's parser could not be loaded (e.g. a missing
        optional dependency), so coverage reporting can be honest about it."""
        self._unavailable[language] = reason

    def get_for_path(self, path: str) -> LanguageParser | None:
        return self._parsers.get(Path(path).suffix.lower())

    def supported_extensions(self) -> frozenset[str]:
        return frozenset(self._parsers.keys())

    def unavailable_languages(self) -> dict[str, str]:
        return dict(self._unavailable)


def build_default_registry() -> ParserRegistry:
    """Build the registry RepoLens ships with.

    Tree-sitter grammar packages are declared dependencies, but this still
    degrades gracefully (recording the language as unavailable rather than
    crashing) if one is missing in a given environment -- parser coverage
    must always be something the caller can inspect, never something that
    silently fails.
    """
    registry = ParserRegistry()

    from repolens_parser.python_parser import PythonParser

    registry.register(PythonParser())

    try:
        from repolens_parser.treesitter_parser import (
            JavaScriptParser,
            TsxParser,
            TypeScriptParser,
        )
    except ImportError as exc:
        registry.mark_unavailable("javascript/typescript", str(exc))
    else:
        registry.register(JavaScriptParser())
        registry.register(TypeScriptParser())
        registry.register(TsxParser())

    return registry
