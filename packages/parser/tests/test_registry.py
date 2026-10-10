from repolens_parser.coverage import describe_coverage
from repolens_parser.registry import build_default_registry


def test_default_registry_supports_python_and_ts_family() -> None:
    registry = build_default_registry()
    assert registry.get_for_path("app.py") is not None
    assert registry.get_for_path("app.js") is not None
    assert registry.get_for_path("app.ts") is not None
    assert registry.get_for_path("app.tsx") is not None
    assert registry.get_for_path("app.unknownext") is None


def test_coverage_report_is_honest_about_extraction() -> None:
    registry = build_default_registry()
    coverage = describe_coverage(registry)
    by_language = {c.language: c for c in coverage}
    assert "python" in by_language
    assert by_language["python"].available is True
    assert "classes" in by_language["python"].extracted
    assert by_language["python"].limitations  # never claims zero limitations
