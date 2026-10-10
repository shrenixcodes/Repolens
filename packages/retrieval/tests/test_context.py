from repolens_retrieval.context import assemble_context
from repolens_retrieval.models import RetrievedChunk


def _chunk(content: str, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        file_path="a.py",
        symbol_qualified_name="f",
        start_line=1,
        end_line=1,
        content=content,
        score=score,
    )


def test_keeps_chunks_within_budget() -> None:
    chunks = [_chunk("x" * 100, 1.0), _chunk("y" * 100, 0.9)]
    assembled = assemble_context(chunks, max_chars=1000)
    assert len(assembled) == 2


def test_stops_before_exceeding_budget() -> None:
    chunks = [_chunk("x" * 100, 1.0), _chunk("y" * 100, 0.9), _chunk("z" * 100, 0.8)]
    assembled = assemble_context(chunks, max_chars=150)
    assert len(assembled) == 1


def test_always_keeps_at_least_the_first_chunk_even_if_oversized() -> None:
    chunks = [_chunk("x" * 5000, 1.0)]
    assembled = assemble_context(chunks, max_chars=100)
    assert len(assembled) == 1


def test_empty_input_returns_empty() -> None:
    assert assemble_context([], max_chars=1000) == []
