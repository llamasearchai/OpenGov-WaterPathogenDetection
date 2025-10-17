"""Additional tests for service error paths and CLI status command."""

import json
from unittest.mock import patch, AsyncMock

import pytest
from typer.testing import CliRunner

from opengovwaterpathogendetection.cli import app
from opengovwaterpathogendetection.services.agent_service import AgentService


runner = CliRunner()


@pytest.mark.asyncio
async def test_agent_service_openai_failure_falls_back(monkeypatch):
    """Force OpenAI client to raise and ensure mock fallback used."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    service = AgentService()

    async def _raise(*a, **k):  # pragma: no cover - ensures path
        raise RuntimeError("boom")

    with patch.object(service, "_run_openai_analysis", side_effect=_raise):
        result = await service.run_analysis("test prompt", provider="openai")
        assert result["provider"] == "mock"
        assert "analysis" in result


@pytest.mark.asyncio
async def test_agent_service_ollama_failure_falls_back(monkeypatch):
    """Force Ollama call failure to ensure fallback to mock analysis."""
    service = AgentService()
    with patch.object(service, "_run_ollama_analysis", side_effect=RuntimeError("ollama down")):
        result = await service.run_analysis("test prompt", model="llama2:7b", provider="ollama")
        assert result["provider"] == "mock"


def test_cli_status_json(monkeypatch):
    """Verify status command returns valid JSON when --json provided."""
    monkeypatch.setenv("OPENAI_API_KEY", "abc123")
    # Ensure settings cache picks up new env variable
    from opengovwaterpathogendetection.core.config import reload_settings
    reload_settings()
    result = runner.invoke(app, ["status", "--json"])  # uses existing app
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert "opengov" in data["app_name"].lower() and "water" in data["app_name"].lower()
    assert isinstance(data["openai_key_set"], bool)
    assert data["openai_key_set"] is True
