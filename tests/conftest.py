"""Pytest configuration and fixtures.

Adds src path for package imports and provides common fixtures.
"""
import sys
from pathlib import Path

# Ensure src directory is on path for editable-like imports if not installed
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from opengovwaterpathogendetection.web.app import app as fastapi_app
from opengovwaterpathogendetection.cli import app as cli_app


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    # Initialize fresh database for tests
    from opengovwaterpathogendetection.core.database import DatabaseManager
    db = DatabaseManager()
    db.initialize(drop_existing=True)
    db.seed_sample_data()
    db.close()

    with TestClient(fastapi_app) as c:
        yield c


@pytest.fixture
def cli_runner():
    """Typer CLI runner fixture."""
    return CliRunner()
