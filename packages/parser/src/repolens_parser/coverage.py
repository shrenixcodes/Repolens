"""Human-readable parser coverage reporting.

The product principle behind this module: RepoLens must never imply it
understood a language construct it didn't actually extract. This is the
single place that states, per language, what is and isn't extracted, so the
CLI/API/web layers can surface it instead of each one hard-coding its own
claims.
"""

from __future__ import annotations

from dataclasses import dataclass

from repolens_parser.registry import ParserRegistry

_KNOWN_LIMITATIONS: dict[str, tuple[str, ...]] = {
    "python": (
        "decorator *arguments* are recorded as source text, not evaluated",
        "relationships are intra-file only -- cross-file resolution happens in repolens_graph",
    ),
    "javascript": (
        "JSDoc comments are not extracted as docstrings",
        "dynamic import() and require() calls are not tracked as imports",
        "relationships are intra-file only -- cross-file resolution happens in repolens_graph",
    ),
    "typescript": (
        "JSDoc comments are not extracted as docstrings",
        "dynamic import() and require() calls are not tracked as imports",
        "generic type parameters are not modeled",
        "relationships are intra-file only -- cross-file resolution happens in repolens_graph",
    ),
    "tsx": (
        "JSDoc comments are not extracted as docstrings",
        "JSX element usage is not tracked as a component reference",
        "relationships are intra-file only -- cross-file resolution happens in repolens_graph",
    ),
}

_EXTRACTED: dict[str, tuple[str, ...]] = {
    "python": ("classes", "functions", "methods", "imports", "calls", "inheritance", "docstrings", "decorators"),
    "javascript": ("classes", "functions", "methods", "imports", "calls", "inheritance"),
    "typescript": (
        "classes",
        "functions",
        "methods",
        "interfaces",
        "type aliases",
        "imports",
        "calls",
        "inheritance",
        "implements",
    ),
    "tsx": (
        "classes",
        "functions",
        "methods",
        "interfaces",
        "type aliases",
        "imports",
        "calls",
        "inheritance",
        "implements",
    ),
}


@dataclass(frozen=True, slots=True)
class LanguageCoverage:
    language: str
    available: bool
    extensions: tuple[str, ...]
    extracted: tuple[str, ...]
    limitations: tuple[str, ...]
    unavailable_reason: str | None = None


def describe_coverage(registry: ParserRegistry) -> list[LanguageCoverage]:
    """Summarize what each registered parser extracts, plus known gaps."""
    by_language: dict[str, set[str]] = {}
    for ext in registry.supported_extensions():
        parser = registry.get_for_path(f"x{ext}")
        if parser is None:
            continue
        by_language.setdefault(parser.language, set()).add(ext)

    reports = [
        LanguageCoverage(
            language=language,
            available=True,
            extensions=tuple(sorted(exts)),
            extracted=_EXTRACTED.get(language, ()),
            limitations=_KNOWN_LIMITATIONS.get(language, ()),
        )
        for language, exts in by_language.items()
    ]

    for language, reason in registry.unavailable_languages().items():
        reports.append(
            LanguageCoverage(
                language=language,
                available=False,
                extensions=(),
                extracted=(),
                limitations=(),
                unavailable_reason=reason,
            )
        )

    reports.sort(key=lambda r: r.language)
    return reports
