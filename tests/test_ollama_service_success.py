"""Success path tests for OllamaService (run_model, list_models)."""
from __future__ import annotations

from unittest.mock import patch
import pytest

from opengovwaterpathogendetection.services.ollama_service import OllamaService


@pytest.mark.asyncio
async def test_ollama_run_model_success():
    service = OllamaService()

    async def fake_post(url, json):  # noqa: ANN001
        class R:
            status_code = 200
            def json(self):
                return {"response": "hello world"}
        return R()

    with patch("httpx.AsyncClient.post", side_effect=fake_post):
        text = await service.run_model("prompt", model="llama2:7b")
        assert text == "hello world"


@pytest.mark.asyncio
async def test_ollama_list_models_success():
    service = OllamaService()

    async def fake_get(url):  # noqa: ANN001
        class R:
            status_code = 200
            def json(self):
                return {"models": [{"name": "llama2:7b"}]}
        return R()

    with patch("httpx.AsyncClient.get", side_effect=fake_get):
        models = await service.list_models()
        assert models and models[0]["name"] == "llama2:7b"
