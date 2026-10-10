from repolens_indexer.chunking import build_chunks
from repolens_parser.python_parser import PythonParser


def test_chunks_one_per_top_level_symbol() -> None:
    source = "def foo():\n    return 1\n\n\ndef bar():\n    return 2\n"
    result = PythonParser().parse("a.py", source)
    chunks = build_chunks(source, result.symbols)
    names = {c.symbol_qualified_name for c in chunks}
    assert names == {"foo", "bar"}


def test_chunk_content_matches_symbol_lines() -> None:
    source = "def foo():\n    return 1\n"
    result = PythonParser().parse("a.py", source)
    chunks = build_chunks(source, result.symbols)
    assert len(chunks) == 1
    assert chunks[0].content == "def foo():\n    return 1"
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 2


def test_file_with_no_symbols_gets_one_whole_file_chunk() -> None:
    source = "# just a markdown file\nwith some text\n"
    chunks = build_chunks(source, [])
    assert len(chunks) == 1
    assert chunks[0].symbol_qualified_name is None
    assert chunks[0].content == source


def test_empty_file_produces_no_chunks() -> None:
    assert build_chunks("", []) == []
    assert build_chunks("   \n  ", []) == []


def test_variables_are_not_chunked_separately() -> None:
    source = "CONFIG = {}\n\ndef foo():\n    return 1\n"
    result = PythonParser().parse("a.py", source)
    chunks = build_chunks(source, result.symbols)
    names = {c.symbol_qualified_name for c in chunks}
    assert names == {"foo"}
