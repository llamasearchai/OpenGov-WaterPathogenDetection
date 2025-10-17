"""Tests for OllamaService error and success paths."""

from unittest.mock import patch, AsyncMock
import pytest

from opengovwaterpathogendetection.services.ollama_service import OllamaService


@pytest.mark.asyncio
async def test_ollama_list_models_failure(monkeypatch):
    service = OllamaService()
    async def fake_get(url):
        class R:
            status_code = 500
            def json(self):
                return {}
        return R()
    with patch("httpx.AsyncClient.get", side_effect=fake_get):
        models = await service.list_models()
        assert models == []


@pytest.mark.asyncio
async def test_ollama_check_connection_false(monkeypatch):
    service = OllamaService()
    with patch("httpx.AsyncClient.get", side_effect=Exception("down")):
        ok = await service.check_connection()
        assert ok is False


@pytest.mark.asyncio
async def test_ollama_run_model_failure(monkeypatch):
    service = OllamaService()
    async def fake_post(url, json, timeout=300):  # noqa: A002
        class R:
            status_code = 500
            def json(self):
                return {"response": ""}
        return R()
    with patch("httpx.AsyncClient.post", side_effect=fake_post):
        with pytest.raises(Exception):
            await service.run_model("prompt")
