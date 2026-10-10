import httpx
import pytest

from repolens_ai.embeddings.ollama import OllamaEmbeddingProvider
from repolens_shared.exceptions import ProviderError


def _patch_post(monkeypatch, handler) -> None:
    def fake_post(url, *, json=None, timeout=None, **kwargs):
        request = httpx.Request("POST", url, json=json)
        response = handler(request, json)
        response.request = request
        return response

    monkeypatch.setattr(httpx, "post", fake_post)


def test_embed_batch_calls_ollama_embed_endpoint(monkeypatch) -> None:
    captured = {}

    def handler(request, body):
        captured["url"] = str(request.url)
        captured["body"] = body
        return httpx.Response(200, json={"embeddings": [[0.1, 0.2], [0.3, 0.4]]})

    _patch_post(monkeypatch, handler)
    provider = OllamaEmbeddingProvider(model="nomic-embed-text", dimensions=2)

    result = provider.embed_batch(["a", "b"])

    assert result == [[0.1, 0.2], [0.3, 0.4]]
    assert captured["url"] == "http://localhost:11434/api/embed"
    assert captured["body"] == {"model": "nomic-embed-text", "input": ["a", "b"]}


def test_embed_single_text_uses_batch_endpoint(monkeypatch) -> None:
    def handler(request, body):
        return httpx.Response(200, json={"embeddings": [[1.0, 2.0]]})

    _patch_post(monkeypatch, handler)
    provider = OllamaEmbeddingProvider(model="m", dimensions=2)
    assert provider.embed("hello") == [1.0, 2.0]


def test_http_error_raises_provider_error(monkeypatch) -> None:
    def handler(request, body):
        return httpx.Response(500, json={"error": "boom"})

    _patch_post(monkeypatch, handler)
    provider = OllamaEmbeddingProvider(model="m", dimensions=2)
    with pytest.raises(ProviderError):
        provider.embed("hello")


def test_malformed_response_raises_provider_error(monkeypatch) -> None:
    def handler(request, body):
        return httpx.Response(200, json={"unexpected": "shape"})

    _patch_post(monkeypatch, handler)
    provider = OllamaEmbeddingProvider(model="m", dimensions=2)
    with pytest.raises(ProviderError):
        provider.embed("hello")


def test_empty_batch_short_circuits_without_request(monkeypatch) -> None:
    def handler(request, body):
        raise AssertionError("should not be called for an empty batch")

    _patch_post(monkeypatch, handler)
    provider = OllamaEmbeddingProvider(model="m", dimensions=2)
    assert provider.embed_batch([]) == []


def test_custom_base_url_is_respected(monkeypatch) -> None:
    captured = {}

    def handler(request, body):
        captured["url"] = str(request.url)
        return httpx.Response(200, json={"embeddings": [[0.0]]})

    _patch_post(monkeypatch, handler)
    provider = OllamaEmbeddingProvider(
        model="m", dimensions=1, base_url="http://my-ollama-host:11434/"
    )
    provider.embed("x")
    assert captured["url"] == "http://my-ollama-host:11434/api/embed"
