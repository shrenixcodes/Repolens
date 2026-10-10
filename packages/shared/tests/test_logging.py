from repolens_shared.logging import redact


def test_redact_hides_api_key_value() -> None:
    message = "Calling provider with api_key=sk-abcdef1234567890"
    result = redact(message)
    assert "sk-abcdef1234567890" not in result
    assert "api_key=[REDACTED]" in result


def test_redact_hides_bearer_token() -> None:
    message = "Authorization: Bearer abc.def.ghi"
    result = redact(message)
    assert "abc.def.ghi" not in result


def test_redact_leaves_unrelated_text_untouched() -> None:
    message = "Indexed 42 files in src/auth/service.py"
    assert redact(message) == message
