"""Deterministic content hashing used for incremental indexing."""

from __future__ import annotations

import hashlib


def content_hash(data: bytes) -> str:
    """Return a stable hex digest for ``data``.

    Used to detect whether a file's content changed between index runs
    without relying on filesystem mtimes, which are unreliable across
    clones, checkouts, and CI caches.
    """
    return hashlib.sha256(data).hexdigest()


def text_hash(text: str) -> str:
    return content_hash(text.encode("utf-8"))
