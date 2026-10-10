import httpx
import pytest

from repolens_ai.llm.openai_compatible import OpenAICompatibleLLMProvider
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
        OpenAICompatibleLLMProvider(
            provider_name="openai_compatible", model="m", base_url=None, api_key=None
        )


def test_generate_sends_messages_and_parses_response(monkeypatch) -> None:
    captured = {}

    def handler(request, body):
        captured["body"] = body
        captured["headers"] = dict(request.headers)
        return httpx.Response(
            200, json={"choices": [{"message": {"content": "Auth happens in auth.py"}}]}
        )

    _patch_post(monkeypatch, handler)
    provider = OpenAICompatibleLLMProvider(
        provider_name="openai", model="gpt-4o-mini", base_url=None, api_key="sk-test"
    )
    result = provider.generate("Where is auth?", system="You are a code assistant")

    assert result == "Auth happens in auth.py"
    assert captured["body"]["messages"][0] == {
        "role": "system",
        "content": "You are a code assistant",
    }
    assert captured["headers"]["authorization"] == "Bearer sk-test"


def test_malformed_response_raises_provider_error(monkeypatch) -> None:
    def handler(request, body):
        return httpx.Response(200, json={"nope": True})

    _patch_post(monkeypatch, handler)
    provider = OpenAICompatibleLLMProvider(
        provider_name="openai", model="m", base_url="https://api.openai.com/v1", api_key="k"
    )
    with pytest.raises(ProviderError):
        provider.generate("hi")


def test_http_error_raises_provider_error(monkeypatch) -> None:
    def handler(request, body):
        return httpx.Response(401, json={"error": "unauthorized"})

    _patch_post(monkeypatch, handler)
    provider = OpenAICompatibleLLMProvider(
        provider_name="openai", model="m", base_url="https://api.openai.com/v1", api_key="bad"
    )
    with pytest.raises(ProviderError):
        provider.generate("hi")
