import httpx
import pytest

from repolens_ai.llm.ollama import OllamaLLMProvider
from repolens_shared.exceptions import ProviderError


def _patch_post(monkeypatch, handler) -> None:
    def fake_post(url, *, json=None, timeout=None, **kwargs):
        request = httpx.Request("POST", url, json=json)
        response = handler(request, json)
        response.request = request
        return response

    monkeypatch.setattr(httpx, "post", fake_post)


def test_generate_calls_ollama_generate_endpoint(monkeypatch) -> None:
    captured = {}

    def handler(request, body):
        captured["url"] = str(request.url)
        captured["body"] = body
        return httpx.Response(200, json={"response": "Auth happens in auth.py"})

    _patch_post(monkeypatch, handler)
    provider = OllamaLLMProvider(model="llama3.1")
    result = provider.generate("Where is auth?", system="You are a code assistant")

    assert result == "Auth happens in auth.py"
    assert captured["url"] == "http://localhost:11434/api/generate"
    assert captured["body"]["model"] == "llama3.1"
    assert captured["body"]["stream"] is False


def test_http_error_raises_provider_error(monkeypatch) -> None:
    def handler(request, body):
        return httpx.Response(500, json={"error": "boom"})

    _patch_post(monkeypatch, handler)
    provider = OllamaLLMProvider(model="m")
    with pytest.raises(ProviderError):
        provider.generate("hi")


def test_malformed_response_raises_provider_error(monkeypatch) -> None:
    def handler(request, body):
        return httpx.Response(200, json={"unexpected": True})

    _patch_post(monkeypatch, handler)
    provider = OllamaLLMProvider(model="m")
    with pytest.raises(ProviderError):
        provider.generate("hi")


def test_stream_yields_single_chunk(monkeypatch) -> None:
    def handler(request, body):
        return httpx.Response(200, json={"response": "full answer"})

    _patch_post(monkeypatch, handler)
    provider = OllamaLLMProvider(model="m")
    assert list(provider.stream("hi")) == ["full answer"]
