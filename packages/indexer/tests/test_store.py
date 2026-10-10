from pathlib import Path

from repolens_indexer.db import IndexStore
from repolens_parser.models import (
    ParsedImport,
    ParsedRelationship,
    ParsedSymbol,
    RelationshipKind,
    SymbolKind,
)
from repolens_shared.types import SourceLocation


def _store(tmp_path: Path) -> IndexStore:
    return IndexStore.open(tmp_path / ".repolens" / "repolens.sqlite3")


def test_upsert_file_assigns_and_reuses_id(tmp_path: Path) -> None:
    store = _store(tmp_path)
    first_id = store.upsert_file(path="a.py", language="python", content_hash="h1", size_bytes=10)
    second_id = store.upsert_file(path="a.py", language="python", content_hash="h2", size_bytes=20)
    assert first_id == second_id

    row = store.get_file("a.py")
    assert row is not None
    assert row.content_hash == "h2"
    assert row.size_bytes == 20


def test_list_files_sorted_by_path(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.upsert_file(path="b.py", language="python", content_hash="h", size_bytes=1)
    store.upsert_file(path="a.py", language="python", content_hash="h", size_bytes=1)
    paths = [f.path for f in store.list_files()]
    assert paths == ["a.py", "b.py"]


def test_replace_file_symbols_persists_and_round_trips_fields(tmp_path: Path) -> None:
    store = _store(tmp_path)
    file_id = store.upsert_file(path="a.py", language="python", content_hash="h", size_bytes=1)

    loc = SourceLocation(path="a.py", start_line=1, end_line=3)
    symbol = ParsedSymbol(
        name="Foo",
        qualified_name="Foo",
        kind=SymbolKind.CLASS,
        location=loc,
        docstring="A class.",
        decorators=("dataclass",),
        is_exported=True,
    )
    store.replace_file_symbols(file_id, [symbol])

    rows = store.list_symbols_for_file(file_id)
    assert len(rows) == 1
    row = rows[0]
    assert row.name == "Foo"
    assert row.kind == "class"
    assert row.docstring == "A class."
    assert row.decorators == ("dataclass",)
    assert row.is_exported is True
    assert row.file_path == "a.py"


def test_replace_file_symbols_clears_previous_rows(tmp_path: Path) -> None:
    store = _store(tmp_path)
    file_id = store.upsert_file(path="a.py", language="python", content_hash="h", size_bytes=1)
    loc = SourceLocation(path="a.py", start_line=1, end_line=1)

    store.replace_file_symbols(
        file_id, [ParsedSymbol("old", "old", SymbolKind.FUNCTION, loc)]
    )
    store.replace_file_symbols(
        file_id, [ParsedSymbol("new", "new", SymbolKind.FUNCTION, loc)]
    )

    names = {r.name for r in store.list_symbols_for_file(file_id)}
    assert names == {"new"}


def test_delete_file_cascades_to_symbols_and_relationships(tmp_path: Path) -> None:
    store = _store(tmp_path)
    file_id = store.upsert_file(path="a.py", language="python", content_hash="h", size_bytes=1)
    loc = SourceLocation(path="a.py", start_line=1, end_line=1)
    store.replace_file_symbols(file_id, [ParsedSymbol("f", "f", SymbolKind.FUNCTION, loc)])
    store.replace_file_relationships(
        file_id,
        [ParsedRelationship(RelationshipKind.CALLS, "<module>", "helper", loc)],
    )

    store.delete_file("a.py")

    assert store.get_file("a.py") is None
    assert store.iter_all_symbols() == []
    assert store.iter_all_relationships() == []


def test_replace_file_relationships_round_trip(tmp_path: Path) -> None:
    store = _store(tmp_path)
    file_id = store.upsert_file(path="a.py", language="python", content_hash="h", size_bytes=1)
    loc = SourceLocation(path="a.py", start_line=5, end_line=5)
    store.replace_file_relationships(
        file_id,
        [ParsedRelationship(RelationshipKind.CALLS, "foo", "helper", loc)],
    )

    rows = store.iter_all_relationships()
    assert len(rows) == 1
    assert rows[0].kind == "calls"
    assert rows[0].resolution == "unresolved"
    assert rows[0].file_path == "a.py"


def test_update_relationship_resolution(tmp_path: Path) -> None:
    store = _store(tmp_path)
    file_id = store.upsert_file(path="a.py", language="python", content_hash="h", size_bytes=1)
    other_file_id = store.upsert_file(path="b.py", language="python", content_hash="h", size_bytes=1)
    loc = SourceLocation(path="a.py", start_line=5, end_line=5)
    store.replace_file_relationships(
        file_id,
        [ParsedRelationship(RelationshipKind.CALLS, "foo", "helper", loc)],
    )
    rel_id = store.iter_all_relationships()[0].id

    other_loc = SourceLocation(path="b.py", start_line=1, end_line=1)
    store.replace_file_symbols(
        other_file_id, [ParsedSymbol("helper", "helper", SymbolKind.FUNCTION, other_loc)]
    )
    target_symbol_id = store.list_symbols_for_file(other_file_id)[0].id

    store.update_relationship_resolution(
        rel_id, target_file_id=other_file_id, target_symbol_id=target_symbol_id
    )

    updated = store.iter_all_relationships()[0]
    assert updated.resolution == "resolved"
    assert updated.target_file_id == other_file_id
    assert updated.target_symbol_id == target_symbol_id


def test_replace_file_imports_round_trip(tmp_path: Path) -> None:
    store = _store(tmp_path)
    file_id = store.upsert_file(path="a.py", language="python", content_hash="h", size_bytes=1)
    loc = SourceLocation(path="a.py", start_line=1, end_line=1)
    store.replace_file_imports(
        file_id, [ParsedImport(module="os", location=loc, imported_names=(), is_relative=False)]
    )
    # calling again should not duplicate rows for the same file
    store.replace_file_imports(
        file_id, [ParsedImport(module="sys", location=loc, imported_names=(), is_relative=False)]
    )
    with store._engine.connect() as conn:
        from repolens_indexer.db.schema import imports_table

        rows = conn.execute(imports_table.select()).fetchall()
    assert len(rows) == 1
    assert rows[0].module == "sys"


def test_schema_is_idempotent_across_reopen(tmp_path: Path) -> None:
    db_path = tmp_path / ".repolens" / "repolens.sqlite3"
    store1 = IndexStore.open(db_path)
    store1.upsert_file(path="a.py", language="python", content_hash="h", size_bytes=1)
    store1.close()

    store2 = IndexStore.open(db_path)
    assert store2.get_file("a.py") is not None
