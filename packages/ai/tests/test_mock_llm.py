from repolens_ai.llm.mock import MockLLMProvider


def test_generate_is_deterministic() -> None:
    provider = MockLLMProvider()
    prompt = "Source: a.py:1\nSource: b.py:2\nQuestion: how does auth work?"
    assert provider.generate(prompt) == provider.generate(prompt)


def test_generate_counts_sources_in_prompt() -> None:
    provider = MockLLMProvider()
    prompt = "Source: a.py:1\nSource: b.py:2\nQuestion: how does auth work?"
    result = provider.generate(prompt)
    assert "2 supporting source(s)" in result


def test_generate_discloses_no_real_model() -> None:
    provider = MockLLMProvider()
    result = provider.generate("Source: a.py:1\n")
    assert "No language model is configured" in result


def test_stream_yields_same_text_as_generate() -> None:
    provider = MockLLMProvider()
    prompt = "Source: a.py:1\n"
    assert list(provider.stream(prompt)) == [provider.generate(prompt)]
