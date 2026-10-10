from repolens_shared.hashing import content_hash, text_hash


def test_text_hash_is_deterministic() -> None:
    assert text_hash("hello world") == text_hash("hello world")


def test_text_hash_differs_for_different_content() -> None:
    assert text_hash("a") != text_hash("b")


def test_content_hash_matches_text_hash_utf8() -> None:
    assert text_hash("café") == content_hash("café".encode())
