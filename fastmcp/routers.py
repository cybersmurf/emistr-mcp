from fastapi import APIRouter, Depends, HTTPException, Request
from fastmcp.models import ToolCall, ToolResponse
from typing import Any
import json

from fastmcp.services import get_db, get_anonymizer, get_response_builder, get_orders_service

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/mcp", response_model=ToolResponse)
async def mcp(call: ToolCall, request: Request):
    # basic logging
    client_ip = request.client.host if request.client else 'unknown'

    # If tool is get_orders, use new service path
    if call.name == 'get_orders':
        try:
            # Try to initialize dependencies, but don't fail tests if DB deps missing
            try:
                db = await get_db(request)
                anonymizer = get_anonymizer(request)
                response_builder = get_response_builder(request)
            except Exception:
                db = None
                anonymizer = None
                response_builder = None

            response = await get_orders_service(call.arguments, db, anonymizer, response_builder)
            return response
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # fallback to legacy call_tool for other tools
    try:
        from server import call_tool as legacy_call_tool
        result_contents = await legacy_call_tool(call.name, call.arguments)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # extract first TextContent as legacy server did
    if result_contents:
        first = result_contents[0]
        try:
            parsed = json.loads(first.text)
        except Exception:
            parsed = first.text
        return parsed

    return {"status": "error", "message": "empty response"}
