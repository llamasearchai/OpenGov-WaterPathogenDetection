"""Success path tests for AgentService covering OpenAI and Ollama branches.

All external HTTP / OpenAI SDK calls are mocked to avoid network usage.
"""
from __future__ import annotations

from unittest.mock import patch, AsyncMock
import pytest

from opengovwaterpathogendetection.services.agent_service import AgentService


@pytest.mark.asyncio
async def test_agent_service_openai_success(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    service = AgentService()

    class FakeChoice:
        def __init__(self, content):
            self.message = type("Msg", (), {"content": content})

    class FakeResponse:
        def __init__(self, text):
            self.choices = [FakeChoice(text)]

    async def fake_create(*a, **k):  # noqa: ANN001, D401
        return FakeResponse('{"analysis": "structured", "provider": "openai", "model": "gpt-4"}')

    with patch.object(service.openai_client.chat.completions, "create", side_effect=fake_create):
        result = await service.run_analysis("prompt", model="gpt-4", provider="openai")
        assert result["provider"] == "openai"
        assert result["analysis"] == "structured"


@pytest.mark.asyncio
async def test_agent_service_ollama_success(monkeypatch):
    service = AgentService()

    async def fake_post(url, json):  # noqa: ANN001
        class R:
            status_code = 200
            def json(self):
                return {"response": '{"analysis": "ollama", "provider": "ollama", "model": "llama2:7b"}'}
        return R()

    with patch("httpx.AsyncClient.post", side_effect=fake_post):
        result = await service.run_analysis("prompt", model="llama2:7b", provider="ollama")
        assert result["provider"] == "ollama"
        assert result["analysis"] == "ollama"
