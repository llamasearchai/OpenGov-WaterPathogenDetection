"""Minimal isolated FastAPI item creation test to diagnose status mismatch."""

from fastapi.testclient import TestClient

from opengovwaterpathogendetection.web.app import app


def test_minimal_create_only():
    client = TestClient(app)
    resp = client.post("/api/items", json={"name": "Mini", "description": "Diag"})
    print("[MINI] status=", resp.status_code, "body=", resp.text)
    assert resp.status_code == 200, resp.text