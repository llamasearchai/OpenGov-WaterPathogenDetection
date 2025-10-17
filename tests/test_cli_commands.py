"""CLI command coverage tests for opengov-water pathogen detection.

These tests exercise the uncovered branches in `cli.py` including:
- status (table output)
- --version flag (root callback path)
- db init (with and without --drop-existing)
- db seed
- agent run (patched to avoid network / AI call)
- serve (patched uvicorn)
- serve-datasette (patched subprocess)
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch
import json

import pytest
from typer.testing import CliRunner

from opengovwaterpathogendetection.cli import app
from opengovwaterpathogendetection.core.config import reload_settings

runner = CliRunner()


def test_cli_status_table(monkeypatch):
    """Ensure status command renders a non-JSON table path."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    reload_settings()
    result = runner.invoke(app, ["status"])  # table variant
    assert result.exit_code == 0, result.output
    assert "OpenGov-WaterPathogenDetection Status" in result.output
    assert "App Name" in result.output or "App Name".lower() in result.output.lower()


def test_cli_version_flag(monkeypatch):
    result = runner.invoke(app, ["--version"])  # triggers root_callback version path
    assert result.exit_code == 0, result.output
    assert "OpenGov-WaterPathogenDetection" in result.output


def test_cli_db_init_and_seed(monkeypatch, tmp_path):
    db_path = tmp_path / "data" / "og.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()

    # init
    r1 = runner.invoke(app, ["db", "init"])  # first time create
    assert r1.exit_code == 0, r1.output
    assert db_path.exists()

    # init drop existing
    r2 = runner.invoke(app, ["db", "init", "--drop-existing"])
    assert r2.exit_code == 0, r2.output

    # seed sample data
    r3 = runner.invoke(app, ["db", "seed"])
    assert r3.exit_code == 0, r3.output
    # simple content assertion
    assert "Database" in r1.output or "initialized" in r1.output


def test_cli_agent_run(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-key")
    reload_settings()

    fake_result = {"analysis": "ok", "provider": "mock", "model": "gpt-4"}

    with patch("opengovwaterpathogendetection.cli.AgentService.run_analysis", return_value=fake_result):
        result = runner.invoke(app, ["agent", "run", "test prompt"])
        assert result.exit_code == 0, result.output
        assert "Analysis Complete" in result.output


def test_cli_serve_and_datasette(monkeypatch, tmp_path):
    """Patch external server runners so we don't actually start services."""
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{tmp_path / 'data' / 'og.db'}")
    reload_settings()

    with patch("uvicorn.run") as uvicorn_run, patch("subprocess.run") as sub_run:
        r_api = runner.invoke(app, ["serve", "--host", "127.0.0.1", "--port", "9100"])
        assert r_api.exit_code == 0, r_api.output
        assert uvicorn_run.called

        r_ds = runner.invoke(app, ["serve-datasette", "--host", "127.0.0.1", "--port", "9800"])
        assert r_ds.exit_code == 0, r_ds.output
        assert sub_run.called
