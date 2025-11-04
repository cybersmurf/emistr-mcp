import json
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Importujeme existující MCP server (ve stejném procesu)
import server as mcp_server
from mcp.types import Tool, TextContent


def parse_optional_int(value: Union[str, int, None]) -> Optional[int]:
    """Parse optional integer from query param - handles empty strings from WebUI."""
    if value is None or value == "" or value == "null":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def parse_optional_bool(value: Union[str, bool, None]) -> Optional[bool]:
    """Parse optional boolean from query param - handles empty strings from WebUI."""
    if value is None or value == "" or value == "null":
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return None

app = FastAPI(title="eMISTR REST/OpenAPI Adapter", version="1.0.0")

# CORS (můžete upravit dle potřeby)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Zvažte omezení na konkrétní origin(y)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pomocné funkce
async def _tool_to_dict(tool: Any) -> Dict[str, Any]:
    try:
        name = getattr(tool, "name", None)
        description = getattr(tool, "description", None)
        input_schema = (
            getattr(tool, "inputSchema", None)
            if getattr(tool, "inputSchema", None) is not None
            else getattr(tool, "input_schema", None)
        )
        if name is not None and description is not None:
            return {
                "name": name,
                "description": description,
                "inputSchema": input_schema or {"type": "object", "properties": {}},
            }
        if isinstance(tool, dict):
            return dict(tool)
    except Exception:
        pass
    return {
        "name": str(getattr(tool, "name", "unknown")),
        "description": str(getattr(tool, "description", "")),
        "inputSchema": {"type": "object", "properties": {}},
    }


async def call_mcp_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    try:
        result_contents = await mcp_server.call_tool(name, arguments)
        if result_contents:
            for item in result_contents:
                if isinstance(item, TextContent):
                    # TextContent.text drží JSON string z MCP
                    return json.loads(item.text)
        # Fallback – prázdný výsledek
        return {"status": "error", "message": "Empty MCP response"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MCP tool error: {e}")


# Startup: zainicializujeme DB a pomocníky MCP serveru (bez spouštění jeho aiohttp serveru)
@app.on_event("startup")
async def on_startup():
    await mcp_server.initialize()


# Základní modely (pouze pro dokumentaci v OpenAPI)
class OrdersQuery(BaseModel):
    status: Optional[str] = ""
    customer_id: Optional[int] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    limit: Optional[int] = 50
    offset: Optional[int] = 0
    columns: Optional[List[str]] = None


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/tools")
async def list_tools():
    tools = await mcp_server.list_tools()
    as_dicts = [await _tool_to_dict(t) for t in tools]
    return {"tools": as_dicts}


@app.get("/orders")
async def get_orders(
    status: Optional[str] = Query(default=None),
    customer_id: Optional[str] = Query(default=None),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    limit: Optional[str] = Query(default=None),
    offset: Optional[str] = Query(default=None),
    columns: Optional[List[str]] = Query(default=None),
):
    # Parse optional integers from WebUI (handles empty strings)
    customer_id_int = parse_optional_int(customer_id)
    limit_int = parse_optional_int(limit)
    offset_int = parse_optional_int(offset)
    
    args: Dict[str, Any] = {
        "status": status or "",
        "limit": limit_int if limit_int is not None else 50,
        "offset": offset_int if offset_int is not None else 0,
    }
    if customer_id_int is not None:
        args["customer_id"] = customer_id_int
    if date_from:
        args["date_from"] = date_from
    if date_to:
        args["date_to"] = date_to
    if columns:
        args["columns"] = columns

    return await call_mcp_tool("get_orders", args)


@app.get("/orders/{order_id}")
async def get_order_detail(order_id: int):
    return await call_mcp_tool("get_order_detail", {"order_id": order_id})


@app.get("/orders:search")
async def search_orders(search_term: str = Query(...), limit: Optional[str] = Query(default=None)):
    limit_int = parse_optional_int(limit)
    return await call_mcp_tool("search_orders", {"search_term": search_term, "limit": limit_int if limit_int is not None else 20})


@app.get("/workers")
async def get_workers(
    status: Optional[str] = Query(default=None),
    group_name: Optional[str] = Query(default=None),
    limit: Optional[str] = Query(default=None),
):
    limit_int = parse_optional_int(limit)
    args: Dict[str, Any] = {
        "status": status or "",
        "limit": limit_int if limit_int is not None else 50
    }
    if group_name:
        args["group_name"] = group_name
    return await call_mcp_tool("get_workers", args)


@app.get("/workers/{worker_id}")
async def get_worker_detail(worker_id: int):
    return await call_mcp_tool("get_worker_detail", {"worker_id": worker_id})


@app.get("/materials")
async def get_materials(low_stock_only: Optional[str] = Query(default=None), limit: Optional[str] = Query(default=None)):
    low_stock_bool = parse_optional_bool(low_stock_only)
    limit_int = parse_optional_int(limit)
    return await call_mcp_tool("get_materials", {
        "low_stock_only": low_stock_bool if low_stock_bool is not None else False,
        "limit": limit_int if limit_int is not None else 50
    })


@app.get("/materials/movements")
async def get_material_movements(
    material_id: Optional[str] = Query(default=None),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    limit: Optional[str] = Query(default=None),
):
    material_id_int = parse_optional_int(material_id)
    limit_int = parse_optional_int(limit)
    args: Dict[str, Any] = {"limit": limit_int if limit_int is not None else 100}
    if material_id_int is not None:
        args["material_id"] = material_id_int
    if date_from:
        args["date_from"] = date_from
    if date_to:
        args["date_to"] = date_to
    return await call_mcp_tool("get_material_movements", args)


@app.get("/operations")
async def get_operations(operation_group: Optional[str] = Query(default=None), limit: Optional[str] = Query(default=None)):
    limit_int = parse_optional_int(limit)
    args: Dict[str, Any] = {"limit": limit_int if limit_int is not None else 50}
    if operation_group:
        args["operation_group"] = operation_group
    return await call_mcp_tool("get_operations", args)


@app.get("/machines")
async def get_machines(status_filter: Optional[str] = Query(default=None), limit: Optional[str] = Query(default=None)):
    limit_int = parse_optional_int(limit)
    args: Dict[str, Any] = {"limit": limit_int if limit_int is not None else 50}
    if status_filter:
        args["status_filter"] = status_filter
    return await call_mcp_tool("get_machines", args)


@app.get("/production/stats")
async def get_production_stats(date_from: str = Query(...), date_to: str = Query(...)):
    return await call_mcp_tool("get_production_stats", {"date_from": date_from, "date_to": date_to})


# Lokální spuštění: uvicorn api_adapter:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api_adapter:app", host="0.0.0.0", port=8000, reload=True)
