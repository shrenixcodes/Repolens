from repolens_shared.types import Citation, SourceLocation


def test_source_location_single_line_str() -> None:
    loc = SourceLocation(path="src/auth/service.py", start_line=42, end_line=42)
    assert str(loc) == "src/auth/service.py:42"


def test_source_location_range_str() -> None:
    loc = SourceLocation(path="src/auth/service.py", start_line=42, end_line=78)
    assert str(loc) == "src/auth/service.py:42-78"


def test_citation_optional_fields_default_none() -> None:
    loc = SourceLocation(path="a.py", start_line=1, end_line=1)
    citation = Citation(location=loc)
    assert citation.symbol_name is None
    assert citation.excerpt is None
