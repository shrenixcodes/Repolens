"""Stable node-id schemes for files and symbols.

A symbol's qualified name alone is not unique across a repository (two
files can each define a function named ``main``), so symbol node ids
include the defining file's path.
"""

from __future__ import annotations

FILE_PREFIX = "file::"
SYMBOL_PREFIX = "symbol::"


def file_node_id(path: str) -> str:
    return f"{FILE_PREFIX}{path}"


def symbol_node_id(path: str, qualified_name: str) -> str:
    return f"{SYMBOL_PREFIX}{path}::{qualified_name}"


def is_file_node(node_id: str) -> bool:
    return node_id.startswith(FILE_PREFIX)


def is_symbol_node(node_id: str) -> bool:
    return node_id.startswith(SYMBOL_PREFIX)
