from pathlib import Path

from click.testing import CliRunner

from repolens_cli.main import cli
from repolens_config import load_config
from repolens_indexer.db import IndexStore
from repolens_indexer.pipeline import index_db_path


def test_index_with_embeddings_enabled_uses_mock_provider_offline(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("def foo():\n    return 1\n", encoding="utf-8")
    (tmp_path / "repolens.yaml").write_text(
        "indexing:\n  enable_embeddings: true\n", encoding="utf-8"
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["index", "--repo", str(tmp_path)])
    assert result.exit_code == 0

    config = load_config(tmp_path)
    store = IndexStore.open(index_db_path(tmp_path, config))
    rows = store.iter_embeddings(provider="mock", model=config.embedding.model)
    assert any(r.symbol_qualified_name == "foo" and r.file_path == "app.py" for r in rows)
