"""File discovery and incremental indexing pipeline for RepoLens."""

from repolens_indexer.discovery import DiscoveredFile, discover_files
from repolens_indexer.embeddings import SemanticSearchResult, semantic_search
from repolens_indexer.pipeline import EmbeddingBackend, IndexResult, index_db_path, run_index
from repolens_indexer.search import LexicalSearchResult, search_lexical
from repolens_indexer.status import IndexStatus, get_status

__all__ = [
    "DiscoveredFile",
    "EmbeddingBackend",
    "IndexResult",
    "IndexStatus",
    "LexicalSearchResult",
    "SemanticSearchResult",
    "discover_files",
    "get_status",
    "index_db_path",
    "run_index",
    "search_lexical",
    "semantic_search",
]
