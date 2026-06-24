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


def test_database_engine_works_with_postgresql_url(monkeypatch):
    """Verify engine creation doesn't crash with a PostgreSQL-like URL format."""
    original_url = config.DATABASE_URL
    pg_url = "postgresql://user:password@host:5432/dbname"

    monkeypatch.setattr(config, "DATABASE_URL", pg_url)
    try:
        importlib.reload(crud)
        assert crud.engine.dialect.name == "postgresql"
    finally:
        monkeypatch.setattr(config, "DATABASE_URL", original_url)
        importlib.reload(crud)
