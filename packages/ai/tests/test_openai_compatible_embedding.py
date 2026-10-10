import httpx
import pytest

from repolens_ai.embeddings.openai_compatible import OpenAICompatibleEmbeddingProvider
from repolens_shared.exceptions import ConfigurationError, ProviderError


def _patch_post(monkeypatch, handler) -> None:
    def fake_post(url, *, json=None, headers=None, timeout=None, **kwargs):
        request = httpx.Request("POST", url, json=json, headers=headers)
        response = handler(request, json)
        response.request = request
        return response

    monkeypatch.setattr(httpx, "post", fake_post)


def test_openai_compatible_requires_base_url() -> None:
    with pytest.raises(ConfigurationError):
        OpenAICompatibleEmbeddingProvider(
            provider_name="openai_compatible",
            model="m",
            base_url=None,
            api_key=None,
            dimensions=4,
        )


def test_openai_provider_defaults_base_url() -> None:
    provider = OpenAICompatibleEmbeddingProvider(
        provider_name="openai", model="text-embedding-3-small", base_url=None, api_key="sk-x", dimensions=4
    )
    assert provider._base_url == "https://api.openai.com/v1"


def test_embed_batch_sends_auth_header_and_parses_response(monkeypatch) -> None:
    captured = {}

    def handler(request, body):
        captured["headers"] = dict(request.headers)
        captured["body"] = body
        return httpx.Response(200, json={"data": [{"embedding": [0.1, 0.2]}, {"embedding": [0.3, 0.4]}]})

    _patch_post(monkeypatch, handler)
    provider = OpenAICompatibleEmbeddingProvider(
        provider_name="openai",
        model="text-embedding-3-small",
        base_url="https://api.openai.com/v1",
        api_key="sk-test",
        dimensions=2,
    )
    result = provider.embed_batch(["a", "b"])

    assert result == [[0.1, 0.2], [0.3, 0.4]]
    assert captured["headers"]["authorization"] == "Bearer sk-test"
    assert captured["body"] == {"model": "text-embedding-3-small", "input": ["a", "b"]}


def test_local_server_without_api_key_omits_auth_header(monkeypatch) -> None:
    captured = {}

    def handler(request, body):
        captured["has_auth"] = "authorization" in request.headers
        return httpx.Response(200, json={"data": [{"embedding": [0.0]}]})

    _patch_post(monkeypatch, handler)
    provider = OpenAICompatibleEmbeddingProvider(
        provider_name="openai_compatible",
        model="m",
        base_url="http://localhost:1234/v1",
        api_key=None,
        dimensions=1,
    )
    provider.embed("x")
    assert captured["has_auth"] is False


def test_malformed_response_raises_provider_error(monkeypatch) -> None:
    def handler(request, body):
        return httpx.Response(200, json={"nope": True})

    _patch_post(monkeypatch, handler)
    provider = OpenAICompatibleEmbeddingProvider(
        provider_name="openai", model="m", base_url="https://api.openai.com/v1", api_key="k", dimensions=1
    )
    with pytest.raises(ProviderError):
        provider.embed("x")


def test_http_error_raises_provider_error(monkeypatch) -> None:
    def handler(request, body):
        return httpx.Response(401, json={"error": "unauthorized"})

    _patch_post(monkeypatch, handler)
    provider = OpenAICompatibleEmbeddingProvider(
        provider_name="openai", model="m", base_url="https://api.openai.com/v1", api_key="bad", dimensions=1
    )
    with pytest.raises(ProviderError):
        provider.embed("x")
