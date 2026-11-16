"""Structural checks for the side migration's legacy-row handling."""

import importlib.util
from pathlib import Path

import sqlalchemy as sa


def test_migration_backfills_existing_rows_as_unspecified(monkeypatch):
    path = Path(__file__).parents[2] / "alembic" / "versions" / "003_historical_price_side.py"
    spec = importlib.util.spec_from_file_location("historical_price_side_migration", path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    calls = []

    class Operations:
        def __getattr__(self, name):
            def record(*args, **kwargs):
                calls.append((name, args, kwargs))
            return record

    monkeypatch.setattr(migration, "op", Operations())
    migration.upgrade()

    add_column = next(call for call in calls if call[0] == "add_column")
    column = add_column[1][1]
    assert column.name == "price_side"
    assert column.nullable is False
    assert str(column.server_default.arg) == "unspecified"

    unique = next(call for call in calls if call[0] == "create_unique_constraint")
    assert unique[1][2] == ["symbol", "timeframe", "price_side", "timestamp"]
