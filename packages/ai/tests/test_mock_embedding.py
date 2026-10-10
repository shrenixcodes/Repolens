from repolens_ai.embeddings.mock import MockEmbeddingProvider


def test_embed_is_deterministic() -> None:
    provider = MockEmbeddingProvider(dimensions=64)
    assert provider.embed("hello world") == provider.embed("hello world")


def test_embed_returns_correct_dimensions() -> None:
    provider = MockEmbeddingProvider(dimensions=64)
    assert len(provider.embed("anything")) == 64


def test_embed_is_unit_normalized() -> None:
    provider = MockEmbeddingProvider(dimensions=64)
    vector = provider.embed("some text with several words")
    norm_sq = sum(v * v for v in vector)
    assert abs(norm_sq - 1.0) < 1e-6


def test_empty_text_returns_zero_vector() -> None:
    provider = MockEmbeddingProvider(dimensions=32)
    assert provider.embed("") == [0.0] * 32


def test_shared_words_increase_similarity() -> None:
    provider = MockEmbeddingProvider(dimensions=256)
    a = provider.embed("jwt token authentication login")
    b = provider.embed("jwt token verification handler")
    c = provider.embed("completely unrelated grocery shopping list")

    def cosine(x: list[float], y: list[float]) -> float:
        return sum(xi * yi for xi, yi in zip(x, y, strict=True))

    assert cosine(a, b) > cosine(a, c)


def test_embed_batch_matches_individual_embed() -> None:
    provider = MockEmbeddingProvider(dimensions=32)
    texts = ["alpha", "beta", "gamma"]
    batch = provider.embed_batch(texts)
    individual = [provider.embed(t) for t in texts]
    assert batch == individual
