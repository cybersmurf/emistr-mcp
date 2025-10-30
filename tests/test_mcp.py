import asyncio
import json
import sys
import os
import pytest
from aiohttp import web

# Add repository root to sys.path so 'server' can be imported
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import server


@pytest.fixture
async def app(aiohttp_client):
    # Patch server globals with fakes to avoid real DB dependencies
    class FakeDB:
        async def connect(self):
            return None

        async def get_orders(self, **kwargs):
            return [{"id": 1, "code": "2024/001"}]

    class FakeAnonymizer:
        def anonymize_orders(self, data):
            return data

    class FakeResponseBuilder:
        def build_orders_response(self, data, args):
            return {"status": "success", "data": {"items": data}}

    server._db = FakeDB()
    server._anonymizer = FakeAnonymizer()
    server._response_builder = FakeResponseBuilder()

    app = web.Application()
    app.router.add_post('/mcp', server.mcp_handler)
    app.router.add_get('/health', lambda request: web.json_response({"status": "ok"}))
    return app


@pytest.mark.asyncio
async def test_health(aiohttp_client, app):
    client = await aiohttp_client(app)
    resp = await client.get('/health')
    assert resp.status == 200
    data = await resp.json()
    assert data['status'] == 'ok'


@pytest.mark.asyncio
async def test_mcp_valid(aiohttp_client, app):
    client = await aiohttp_client(app)
    payload = {"name": "get_orders", "arguments": {}}
    resp = await client.post('/mcp', json=payload)
    assert resp.status == 200
    data = await resp.json()
    assert data.get('status') == 'success'


@pytest.mark.asyncio
async def test_mcp_wrong_content_type(aiohttp_client, app):
    client = await aiohttp_client(app)
    resp = await client.post('/mcp', data='test', headers={'Content-Type': 'text/plain'})
    assert resp.status == 415


@pytest.mark.asyncio
async def test_mcp_empty_body(aiohttp_client, app):
    client = await aiohttp_client(app)
    resp = await client.post('/mcp', data='', headers={'Content-Type': 'application/json'})
    assert resp.status == 400
