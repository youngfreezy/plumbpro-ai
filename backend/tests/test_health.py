"""Smoke test for the /api/health endpoint."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.gateway.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_health_returns_200(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
