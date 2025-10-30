#!/usr/bin/env python3
"""
eMISTR MCP Server
Provides AI assistants access to eMISTR ERP via MCP protocol
"""

import asyncio
import json
import logging
from typing import Any, Sequence, Mapping, List, Dict
from mcp.server import Server
from mcp.types import Tool, TextContent
from aiohttp import web

from database import DatabaseManager
from anonymizer import DataAnonymizer
from response_builder import ResponseBuilder
from config import Config

# Logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('emistr-mcp')

# MCP server instance (decorators use this)
app = Server("emistr-mcp")

# Globals
config: Config = None
_db: DatabaseManager = None
_anonymizer: DataAnonymizer = None
_response_builder: ResponseBuilder = None
SERVER_VERSION = "0.2.4 beta" # Server version identifier
CLIENT_PROTOCOL_VERSION: str | None = None


async def _get_server_offerings() -> Dict[str, Any]:
    tools_list = await list_tools()
    tools_dicts = [tool.to_dict() if hasattr(tool, 'to_dict') else tool for tool in tools_list]
    protocol_version = CLIENT_PROTOCOL_VERSION or "2025-03-26"
    return {
        "protocolVersion": protocol_version,
        "capabilities": {
            "tools": {"streamable": False, "searchable": False},
            "resources": {"streamable": False, "searchable": False},
            "embedding": False
        },
        "serverInfo": {
            "name": "emistr-mcp",
            "version": SERVER_VERSION,
            "description": "eMISTR MCP Server providing access to eMISTR ERP via MCP protocol."
        },
        "tools": tools_dicts,
        "resources": [],
        "prompts": []
    }


async def initialize() -> None:
    """Initialize configuration, database and helpers."""
    global config, _db, _anonymizer, _response_builder

    config = Config()
    _db = DatabaseManager(config)
    _anonymizer = DataAnonymizer(config)
    _response_builder = ResponseBuilder()

    await _db.connect()
    logger.info(f"eMISTR MCP Server {SERVER_VERSION} initialized")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """Return the list of available tools (expanded from old version)."""
    return [
        Tool(
            name="initialize",
            description="Initializes the MCP client and returns server capabilities.",
            inputSchema={"type": "object", "properties": {}} # Minimal input schema
        ),
        Tool(
            name="get_orders",
            description="Získá seznam zakázek.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Maximální počet zakázek k vrácení"},
                    "offset": {"type": "integer", "description": "Počet zakázek k přeskočení"},
                    "status": {"type": "string", "description": "Filtr podle statusu"},
                    "customer_id": {"type": "integer", "description": "ID zákazníka"},
                    "date_from": {"type": "string", "description": "Datum od (YYYY-MM-DD)"},
                    "date_to": {"type": "string", "description": "Datum do (YYYY-MM-DD)"}
                }
            }
        ),
        Tool(
            name="get_order_detail",
            description="Získá detail zakázky.",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "ID zakázky"}
                },
                "required": ["order_id"]
            }
        ),
        Tool(
            name="search_orders",
            description="Fulltextové vyhledávání v zakázkách podle názvu, kódu, čísla objednávky nebo poznámek.",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_term": {"type": "string"},
                    "limit": {"type": "integer"}
                },
                "required": ["search_term"]
            }
        ),
        Tool(
            name="get_workers",
            description="Získá seznam zaměstnanců s možností filtrování.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "group_name": {"type": "string"},
                    "limit": {"type": "integer"}
                }
            }
        ),
        Tool(
            name="get_worker_detail",
            description="Detail zaměstnance včetně statistik výkonu.",
            inputSchema={
                "type": "object",
                "properties": {
                    "worker_id": {"type": "integer"}
                },
                "required": ["worker_id"]
            }
        ),
        Tool(
            name="get_materials",
            description="Seznam materiálů na skladu.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sklad_id": {"type": "integer"},
                    "low_stock_only": {"type": "boolean"},
                    "limit": {"type": "integer"}
                }
            }
        ),
        Tool(
            name="get_material_movements",
            description="Pohyby materiálu (příjmy/výdeje).",
            inputSchema={
                "type": "object",
                "properties": {
                    "material_id": {"type": "integer"},
                    "date_from": {"type": "string"},
                    "date_to": {"type": "string"},
                    "limit": {"type": "integer"}
                }
            }
        ),
        Tool(
            name="get_operations",
            description="Seznam operací (pracovní postupy).",
            inputSchema={"type": "object", "properties": {"operation_group": {"type": "string"}, "limit": {"type": "integer"}}}
        ),
        Tool(
            name="get_machines",
            description="Seznam strojů a jejich aktuální stav.",
            inputSchema={"type": "object", "properties": {"status_filter": {"type": "string"}, "limit": {"type": "integer"}}}
        ),
        Tool(
            name="get_production_stats",
            description="Statistiky výroby za období.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date_from": {"type": "string"},
                    "date_to": {"type": "string"}
                },
                "required": ["date_from", "date_to"]
            }
        ),
    ]


def _redact_arguments(arguments: Any) -> str:
    """Return a short, non-sensitive representation of arguments for logs."""
    try:
        if isinstance(arguments, Mapping):
            # show keys and value types only
            return ",".join(f"{k}={type(v).__name__}" for k, v in arguments.items())
        return type(arguments).__name__
    except Exception:
        return "<unavailable>"


def _get_client_ip(request: web.Request) -> str:
    """Extract client IP address safely."""
    try:
        if request.remote:
            return request.remote
        if request.transport:
            peer = request.transport.get_extra_info('peername')
            if peer:
                return peer[0]
    except Exception:
        pass
    return "unknown"


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[Any]:
    """Process a tool call (dispatcher)."""
    try:
        logger.info("Tool called: %s args_summary: %s", name, _redact_arguments(arguments))
        logger.debug("Tool full arguments: %r", arguments)

        if name == "initialize":
            offerings = await _get_server_offerings()
            return [TextContent(type="text", text=json.dumps(offerings, ensure_ascii=False))]

        # MCP discovery endpoints
        elif name in ("tools/list", "tools.list"):
            tools_list = await list_tools()
            tools_dicts = [tool.to_dict() if hasattr(tool, 'to_dict') else tool for tool in tools_list]
            return [TextContent(type="text", text=json.dumps({"tools": tools_dicts}, ensure_ascii=False))]

        elif name in ("resources/list", "resources.list"):
            resources: List[Dict[str, Any]] = []
            return [TextContent(type="text", text=json.dumps({"resources": resources}, ensure_ascii=False))]

        elif name in ("notifications/initialized", "notifications.initialized"):
            return [TextContent(type="text", text=json.dumps({}, ensure_ascii=False))]

        elif name == "get_orders":
            # Support optional 'columns' selection at response level
            cols = None
            if isinstance(arguments, Mapping):
                c = arguments.get('columns')
                if isinstance(c, list) and all(isinstance(x, str) for x in c):
                    cols = c
            result = await _db.get_orders(**{k: v for k, v in arguments.items() if k != 'columns'})
            anonymized = _anonymizer.anonymize_orders(result) if hasattr(_anonymizer, 'anonymize_orders') else result
            if cols:
                try:
                    items = anonymized.get('orders') or anonymized.get('items') or []
                    filtered = [ {k: itm.get(k) for k in cols if k in itm} for itm in items ]
                    # Build a shallow copy response with filtered items
                    filtered_payload = dict(anonymized)
                    # normalize to 'orders' key if present, otherwise 'items'
                    if 'orders' in filtered_payload:
                        filtered_payload['orders'] = filtered
                    else:
                        filtered_payload['items'] = filtered
                    response = _response_builder.build_orders_response(filtered_payload, arguments)
                except Exception:
                    logger.exception("Error filtering columns in get_orders response; falling back to full response")
                    response = _response_builder.build_orders_response(anonymized, arguments)
            else:
                response = _response_builder.build_orders_response(anonymized, arguments)

        elif name == "get_order_detail":
            result = await _db.get_order_detail(**arguments)
            anonymized = _anonymizer.anonymize_order_detail(result) if hasattr(_anonymizer, 'anonymize_order_detail') else result
            response = _response_builder.build_order_detail_response(anonymized)

        # Additional tools from old version
        elif name == "search_orders":
            result = await _db.search_orders(**arguments)
            anonymized = _anonymizer.anonymize_orders(result) if hasattr(_anonymizer, 'anonymize_orders') else result
            response = _response_builder.build_search_response(anonymized, arguments) if hasattr(_response_builder, 'build_search_response') else {"result": anonymized}

        elif name == "get_workers":
            result = await _db.get_workers(**arguments)
            anonymized = _anonymizer.anonymize_workers(result) if hasattr(_anonymizer, 'anonymize_workers') else result
            response = _response_builder.build_workers_response(anonymized, arguments) if hasattr(_response_builder, 'build_workers_response') else {"result": anonymized}

        elif name == "get_worker_detail":
            result = await _db.get_worker_detail(**arguments)
            anonymized = _anonymizer.anonymize_worker_detail(result) if hasattr(_anonymizer, 'anonymize_worker_detail') else result
            response = _response_builder.build_worker_detail_response(anonymized) if hasattr(_response_builder, 'build_worker_detail_response') else {"result": anonymized}

        elif name == "get_materials":
            result = await _db.get_materials(**arguments)
            anonymized = _anonymizer.anonymize_materials(result) if hasattr(_anonymizer, 'anonymize_materials') else result
            response = _response_builder.build_materials_response(anonymized, arguments) if hasattr(_response_builder, 'build_materials_response') else {"result": anonymized}

        elif name == "get_material_movements":
            result = await _db.get_material_movements(**arguments)
            response = _response_builder.build_movements_response(result, arguments) if hasattr(_response_builder, 'build_movements_response') else {"result": result}

        elif name == "get_operations":
            result = await _db.get_operations(**arguments)
            response = _response_builder.build_operations_response(result, arguments) if hasattr(_response_builder, 'build_operations_response') else {"result": result}

        elif name == "get_machines":
            result = await _db.get_machines(**arguments)
            response = _response_builder.build_machines_response(result, arguments) if hasattr(_response_builder, 'build_machines_response') else {"result": result}

        elif name == "get_production_stats":
            result = await _db.get_production_stats(**arguments)
            response = _response_builder.build_stats_response(result, arguments) if hasattr(_response_builder, 'build_stats_response') else {"result": result}

        else:
            response = {"status": "error", "message": f"Neznámý tool: {name}"}

        return [TextContent(type="text", text=json.dumps(response, ensure_ascii=False))]

    except Exception:
        logger.exception("Error in tool %s", name)
        error_response = {"status": "error", "message": "Chyba při zpracování"}
        return [TextContent(type="text", text=json.dumps(error_response, ensure_ascii=False))]


async def mcp_post_handler(request: web.Request):
    """HTTP handler for MCP tool calls."""
    client_ip = _get_client_ip(request)

    content_type = (request.content_type or '').lower()
    if 'application/json' not in content_type:
        return web.json_response(
            {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Unsupported Media Type: application/json required"}},
            status=200
        )

    payload_id = None
    try:
        payload = await request.json()
        payload_id = payload.get('id') if 'id' in payload else None
        logger.debug("MCP POST payload from %s: %r", client_ip, payload)
    except Exception:
        logger.warning("MCP HTTP call from %s: malformed JSON payload", client_ip)
        return web.json_response(
            {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Malformed JSON payload"}},
            status=200
        )

    if not isinstance(payload, dict):
        logger.warning("MCP HTTP call from %s: JSON payload is not an object", client_ip)
        return web.json_response(
            {"jsonrpc": "2.0", "id": payload_id, "error": {"code": -32700, "message": "JSON payload must be an object"}},
            status=200
        )

    tool_name = payload.get('method')
    tool_arguments = payload.get('params')
    logger.debug("Parsed method=%r params_type=%s", tool_name, type(tool_arguments).__name__ if tool_arguments is not None else 'None')

    # Fallback: if no method provided, treat as offerings discovery and return capabilities/tools
    if not tool_name:
        try:
            offerings = await _get_server_offerings()
            return web.json_response(
                {
                    "jsonrpc": "2.0",
                    "id": payload_id,
                    "result": {
                        "content": [
                            {"type": "text", "text": json.dumps(offerings, ensure_ascii=False)}
                        ]
                    }
                },
                status=200
            )
        except Exception:
            logger.exception("Error while generating offerings for implicit request")
            return web.json_response({"jsonrpc": "2.0", "id": payload_id, "error": {"code": -32000, "message": "Internal server error during offerings discovery"}}, status=200)

    # Default missing params to empty object
    if tool_arguments is None:
        tool_arguments = {}

    # Capture client protocolVersion if initialize is called
    if tool_name == 'initialize' and isinstance(tool_arguments, Mapping):
        try:
            global CLIENT_PROTOCOL_VERSION
            client_pv = tool_arguments.get('protocolVersion')
            if isinstance(client_pv, str) and client_pv:
                CLIENT_PROTOCOL_VERSION = client_pv
        except Exception:
            pass

    if not tool_name or tool_arguments is None:
        logger.warning("Invalid MCP request from %s: missing 'method' or 'params' - keys: %s", client_ip, list(payload.keys()))
        return web.json_response(
            {"jsonrpc": "2.0", "id": payload_id, "error": {"code": -32602, "message": "Missing 'method' or 'params' in request payload"}},
            status=200
        )

    if not isinstance(tool_arguments, Mapping):
        logger.warning("Invalid MCP request from %s: 'params' must be an object, got %s", client_ip, type(tool_arguments).__name__)
        return web.json_response(
            {"jsonrpc": "2.0", "id": payload_id, "error": {"code": -32602, "message": "'params' must be an object/dictionary"}},
            status=200
        )

    # Handle MCP spec method tools/call -> delegates to our internal tool dispatcher
    if tool_name == 'tools/call':
        inner_name = tool_arguments.get('name') if isinstance(tool_arguments, Mapping) else None
        inner_args = tool_arguments.get('arguments') if isinstance(tool_arguments, Mapping) else None
        if not inner_name:
            return web.json_response(
                {"jsonrpc": "2.0", "id": payload_id, "error": {"code": -32602, "message": "Missing 'name' in tools/call params"}},
                status=200
            )
        if not isinstance(inner_args, Mapping):
            inner_args = {}

        try:
            result_contents = await call_tool(inner_name, inner_args)
        except Exception:
            logger.exception("Error while executing tool %s via tools/call", inner_name)
            return web.json_response(
                {"jsonrpc": "2.0", "id": payload_id, "error": {"code": -32000, "message": f"Internal server error while executing tool {inner_name}"}},
                status=200
            )

        content_items: List[Dict[str, Any]] = []
        if result_contents:
            for item in result_contents:
                if isinstance(item, TextContent):
                    content_items.append({"type": "text", "text": item.text})
                else:
                    content_items.append({"type": getattr(item, 'type', 'unknown'), "text": json.dumps(getattr(item, 'text', ''), ensure_ascii=False) if hasattr(item, 'text') else ""})

        return web.json_response(
            {"jsonrpc": "2.0", "id": payload_id, "result": {"content": content_items}},
            status=200
        )

    logger.info("MCP HTTP call received from %s: %s args_summary: %s", client_ip, tool_name, _redact_arguments(tool_arguments))

    try:
        result_contents = await call_tool(tool_name, tool_arguments)
    except Exception:
        logger.exception("Error while executing tool %s", tool_name)
        return web.json_response(
            {"jsonrpc": "2.0", "id": payload_id, "error": {"code": -32000, "message": f"Internal server error while executing tool {tool_name}"}},
            status=200
        )
    # Primary JSON-RPC success output wrapped in MCP result.content
    content_items: List[Dict[str, Any]] = []
    if result_contents:
        for item in result_contents:
            if isinstance(item, TextContent):
                content_items.append({"type": "text", "text": item.text})
            else:
                # Fallback for non-text content types
                content_items.append({"type": getattr(item, 'type', 'unknown'), "text": json.dumps(getattr(item, 'text', ''), ensure_ascii=False) if hasattr(item, 'text') else ""})

    return web.json_response(
        {"jsonrpc": "2.0", "id": payload_id, "result": {"content": content_items}},
        status=200
    )

async def mcp_get_handler(request: web.Request):
    """HTTP handler for listing available tools at /mcp (plain offerings for GET)."""
    client_ip = _get_client_ip(request)
    logger.info("MCP HTTP call received from %s: list_tools (GET /mcp)", client_ip)

    accept = (request.headers.get('Accept') or request.headers.get('accept') or '').lower()
    try:
        offerings = await _get_server_offerings()
    except Exception:
        logger.exception("Error while listing tools at GET /mcp")
        return web.json_response({"error": "Internal server error during tool listing"}, status=500)

    if 'text/event-stream' in accept:
        # Send offerings as a single SSE data event
        body = f"data: {json.dumps(offerings, ensure_ascii=False)}\n\n"
        return web.Response(text=body, content_type='text/event-stream')

    # Default: return plain offerings JSON (no JSON-RPC envelope on GET)
    return web.json_response(offerings, status=200)

async def list_tools_handler(request: web.Request):
    """HTTP handler for listing available tools (plain offerings)."""
    client_ip = _get_client_ip(request)
    logger.info("MCP HTTP call received from %s: list_tools (GET /mcp/tools)", client_ip)

    try:
        offerings = await _get_server_offerings()
        return web.json_response(offerings, status=200)
    except Exception:
        logger.exception("Error while listing tools")
        return web.json_response({"error": "Internal server error during tool listing"}, status=500)


async def health_handler(request: web.Request):
    return web.json_response({"status": "ok"}, status=200)


async def main() -> None:
    logger.info(f"=== Starting eMISTR MCP Server version {SERVER_VERSION} ===")
    await initialize()

    web_app = web.Application()
    web_app.router.add_get('/health', health_handler)
    web_app.router.add_post('/mcp', mcp_post_handler) # Use new handler for POST
    web_app.router.add_get('/mcp', mcp_get_handler) # New handler for GET /mcp
    web_app.router.add_get('/mcp/tools', list_tools_handler) # Keep existing route for /mcp/tools

    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, host='0.0.0.0', port=9001)
    await site.start()

    logger.info("eMISTR MCP HTTP Server started on port 9001")

    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        logger.info("Shutdown requested, stopping server")
    finally:
        # Attempt DB disconnect
        try:
            disconnect = getattr(_db, 'disconnect', None)
            if disconnect:
                await disconnect()
        except Exception:
            logger.exception("Error while disconnecting DB")
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
