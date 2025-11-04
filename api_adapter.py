import json
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Importujeme existující MCP server (ve stejném procesu)
import server as mcp_server
from mcp.types import Tool, TextContent

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
    status: Optional[str] = Query(default=""),
    customer_id: Optional[int] = Query(default=None),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    limit: Optional[int] = Query(default=50, ge=1, le=1000),
    offset: Optional[int] = Query(default=0, ge=0),
    columns: Optional[List[str]] = Query(default=None),
):
    args: Dict[str, Any] = {
        "status": status or "",
        "customer_id": customer_id,
        "date_from": date_from,
        "date_to": date_to,
        "limit": limit,
        "offset": offset,
    }
    if columns:
        args["columns"] = columns

    return await call_mcp_tool("get_orders", {k: v for k, v in args.items() if v is not None})


@app.get("/orders/{order_id}")
async def get_order_detail(order_id: int):
    return await call_mcp_tool("get_order_detail", {"order_id": order_id})


@app.get("/orders:search")
async def search_orders(search_term: str = Query(...), limit: int = Query(20, ge=1, le=200)):
    return await call_mcp_tool("search_orders", {"search_term": search_term, "limit": limit})


@app.get("/workers")
async def get_workers(
    status: Optional[str] = Query(default=""),
    group_name: Optional[str] = Query(default=None),
    limit: Optional[int] = Query(default=50, ge=1, le=1000),
):
    args: Dict[str, Any] = {"status": status or "", "group_name": group_name, "limit": limit}
    return await call_mcp_tool("get_workers", {k: v for k, v in args.items() if v is not None})


@app.get("/workers/{worker_id}")
async def get_worker_detail(worker_id: int):
    return await call_mcp_tool("get_worker_detail", {"worker_id": worker_id})


@app.get("/materials")
async def get_materials(low_stock_only: Optional[bool] = Query(default=False), limit: Optional[int] = Query(default=50, ge=1, le=1000)):
    return await call_mcp_tool("get_materials", {"low_stock_only": low_stock_only, "limit": limit})


@app.get("/materials/movements")
async def get_material_movements(
    material_id: Optional[int] = Query(default=None),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    limit: Optional[int] = Query(default=100, ge=1, le=2000),
):
    args: Dict[str, Any] = {
        "material_id": material_id,
        "date_from": date_from,
        "date_to": date_to,
        "limit": limit,
    }
    return await call_mcp_tool("get_material_movements", {k: v for k, v in args.items() if v is not None})


@app.get("/operations")
async def get_operations(operation_group: Optional[str] = Query(default=None), limit: Optional[int] = Query(default=50, ge=1, le=1000)):
    args: Dict[str, Any] = {"operation_group": operation_group, "limit": limit}
    return await call_mcp_tool("get_operations", {k: v for k, v in args.items() if v is not None})


@app.get("/machines")
async def get_machines(status_filter: Optional[str] = Query(default=None), limit: Optional[int] = Query(default=50, ge=1, le=1000)):
    args: Dict[str, Any] = {"status_filter": status_filter, "limit": limit}
    return await call_mcp_tool("get_machines", {k: v for k, v in args.items() if v is not None})


@app.get("/production/stats")
async def get_production_stats(date_from: str = Query(...), date_to: str = Query(...)):
    return await call_mcp_tool("get_production_stats", {"date_from": date_from, "date_to": date_to})


# Lokální spuštění: uvicorn api_adapter:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api_adapter:app", host="0.0.0.0", port=8000, reload=True)
