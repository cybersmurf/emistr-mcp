import sys
import os
# Ensure repository root is importable
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from fastapi.testclient import TestClient
from fastmcp.main import app
from unittest.mock import AsyncMock, MagicMock

client = TestClient(app)


def test_health():
    resp = client.get('/health')
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_get_orders(monkeypatch):
    # patch services to avoid DB access
    fake_response = {"status": "success", "data": {"items": [{"id": 1}]}}

    async def fake_get_orders_service(arguments, db, anonymizer, response_builder):
        return fake_response

    monkeypatch.setattr('fastmcp.routers.get_orders_service', fake_get_orders_service)
    resp = client.post('/mcp', json={"name": "get_orders", "arguments": {}})
    assert resp.status_code == 200
    assert resp.json()['status'] == 'success'
