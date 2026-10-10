"""Shared exception hierarchy.

Every RepoLens-specific error should subclass :class:`RepoLensError` so that
API and CLI layers can catch one base type and still distinguish categories
when they need to (e.g. to map to an HTTP status code).
"""

from __future__ import annotations


class RepoLensError(Exception):
    """Base class for all RepoLens-specific errors."""


class PathTraversalError(RepoLensError):
    """Raised when a path would resolve outside of its expected root.

    This is a security boundary error: it must never be silently swallowed,
    and callers must not fall back to using the unsafe path.
    """


class ConfigurationError(RepoLensError):
    """Raised when configuration is missing, invalid, or contradictory."""


class ParserError(RepoLensError):
    """Raised when a source file cannot be parsed by its assigned language parser.

    This represents a single-file failure, not a fatal pipeline error -- the
    indexer should record it and continue with the rest of the repository.
    """


class ProviderError(RepoLensError):
    """Raised when an AI (LLM or embedding) provider call fails.

    Covers connection failures, invalid responses, and provider configuration
    errors. Callers should degrade gracefully (e.g. fall back to lexical-only
    search) rather than crash the whole pipeline when this is raised.
    """


class RepositoryNotIndexedError(RepoLensError):
    """Raised when an operation requires an index that does not exist yet."""


class GitError(RepoLensError):
    """Raised when a Git operation fails or the target is not a Git repository."""
