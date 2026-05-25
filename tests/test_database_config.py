import importlib

import config
import db.crud as crud


def test_database_engine_uses_configured_database_url(monkeypatch, tmp_path):
    original_url = config.DATABASE_URL
    database_url = f"sqlite:///{tmp_path / 'configured.db'}"

    monkeypatch.setattr(config, "DATABASE_URL", database_url)
    importlib.reload(crud)

    try:
        assert str(crud.engine.url) == database_url
    finally:
        monkeypatch.setattr(config, "DATABASE_URL", original_url)
        importlib.reload(crud)
