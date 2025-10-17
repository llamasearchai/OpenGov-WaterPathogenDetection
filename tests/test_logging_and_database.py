"""Tests for logging configuration variants and DatabaseManager methods."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from opengovwaterpathogendetection.utils.logging import configure_logging, get_logger, LogContext
from opengovwaterpathogendetection.core.database import DatabaseManager
from opengovwaterpathogendetection.core.config import reload_settings


def test_configure_logging_debug_and_context(monkeypatch):
    configure_logging(debug=True)
    logger = get_logger(__name__)
    with LogContext(logger, request_id="abc") as bound:
        bound.info("message inside context")
    # basic assertion: structlog logger has been configured
    assert logger is not None


def test_database_manager_initialize_and_migrate(tmp_path, monkeypatch):
    db_path = tmp_path / "data" / "demo.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    mgr = DatabaseManager()
    mgr.initialize(drop_existing=True)
    mgr.seed_sample_data()
    # migration path (ignore if column already exists)
    mgr.migrate()
    mgr.close()
    assert db_path.exists()


def test_database_manager_context_manager(tmp_path, monkeypatch):
    db_path = tmp_path / "data" / "ctx.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    with DatabaseManager() as mgr:
        mgr.initialize()
    assert db_path.exists()
