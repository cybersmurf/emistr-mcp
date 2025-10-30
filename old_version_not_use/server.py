#!/usr/bin/env python3
"""
eMISTR MCP Server
Poskytuje AI asistentům přístup k eMISTR ERP systému přes MCP protokol
"""

import asyncio
import json
import logging
from typing import Any, Sequence
from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
from pydantic import AnyUrl

from database import DatabaseManager
from anonymizer import DataAnonymizer
from response_builder import ResponseBuilder
from config import Config

# Nastavení logování
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('emistr-mcp')

# Inicializace serveru
app = Server("emistr-mcp")

# Globální instance
config: Config = None
db: DatabaseManager = None
anonymizer: DataAnonymizer = None
response_builder: ResponseBuilder = None


async def initialize():
    """Inicializace serveru a připojení k databázi"""
    global config, db, anonymizer, response_builder
    
    config = Config()
    db = DatabaseManager(config)
    anonymizer = DataAnonymizer(config)
    response_builder = ResponseBuilder()
    
    await db.connect()
    logger.info("eMISTR MCP Server initialized")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Vrátí seznam dostupných tools"""
    return [
        # ZAKÁZKY
        Tool(
            name="get_orders",
            description="""
            Získá seznam zakázek s možností filtrování.
            Použití: Když uživatel chce vidět zakázky, například "Zobraz aktivní zakázky" nebo "Které zakázky jsou zpožděné?"
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filtr podle statusu: 'ANO' (aktivní), 'NE' (neaktivní), nebo prázdné pro všechny",
                        "enum": ["ANO", "NE", ""]
                    },
                    "customer_id": {
                        "type": "integer",
                        "description": "ID zákazníka pro filtrování"
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Datum od (YYYY-MM-DD)"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "Datum do (YYYY-MM-DD)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximální počet výsledků",
                        "default": 50
                    }
                }
            }
        ),
        
        Tool(
            name="get_order_detail",
            description="""
            Získá detailní informace o konkrétní zakázce včetně operací, materiálu a dokumentů.
            Použití: "Zobraz detail zakázky 2024/001" nebo "Co je na zakázce číslo 12345?"
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "integer",
                        "description": "ID zakázky (c_order.id)"
                    },
                    "order_code": {
                        "type": "string",
                        "description": "Kód zakázky (c_order.code) - alternativa k order_id"
                    }
                },
                "required": []
            }
        ),
        
        Tool(
            name="search_orders",
            description="""
            Fulltextové vyhledávání v zakázkách podle názvu, kódu, čísla objednávky nebo poznámek.
            Použití: "Najdi zakázku s 'hřídel'" nebo "Vyhledej zakázky obsahující 'urgentní'"
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "search_term": {
                        "type": "string",
                        "description": "Hledaný text"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximální počet výsledků",
                        "default": 20
                    }
                },
                "required": ["search_term"]
            }
        ),
        
        # ZAMĚSTNANCI
        Tool(
            name="get_workers",
            description="""
            Získá seznam zaměstnanců s možností filtrování.
            Použití: "Zobraz aktivní zaměstnance" nebo "Kdo pracuje na směně?"
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filtr podle statusu",
                        "enum": ["ANO", "NE", ""]
                    },
                    "group_name": {
                        "type": "string",
                        "description": "Filtr podle skupiny"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 50
                    }
                }
            }
        ),
        
        Tool(
            name="get_worker_detail",
            description="""
            Detail zaměstnance včetně statistik výkonu.
            Použití: "Zobraz informace o zaměstnanci" nebo "Kolik hodin odpracoval zaměstnanec XYZ?"
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "worker_id": {
                        "type": "integer",
                        "description": "ID zaměstnance"
                    }
                },
                "required": ["worker_id"]
            }
        ),
        
        # MATERIÁL
        Tool(
            name="get_materials",
            description="""
            Seznam materiálů na skladu.
            Použití: "Kolik máme materiálu na skladu?" nebo "Zobraz materiály s nízkou zásobou"
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "sklad_id": {
                        "type": "integer",
                        "description": "ID skladu"
                    },
                    "low_stock_only": {
                        "type": "boolean",
                        "description": "Zobrazit pouze materiály s nízkou zásobou",
                        "default": False
                    },
                    "limit": {
                        "type": "integer",
                        "default": 50
                    }
                }
            }
        ),
        
        Tool(
            name="get_material_movements",
            description="""
            Pohyby materiálu (příjmy/výdeje).
            Použití: "Zobraz pohyby materiálu za poslední týden"
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "material_id": {
                        "type": "integer",
                        "description": "ID materiálu"
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Datum od"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "Datum do"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 100
                    }
                }
            }
        ),
        
        # OPERACE
        Tool(
            name="get_operations",
            description="""
            Seznam operací (pracovní postupy).
            Použití: "Jaké operace máme definované?" nebo "Zobraz operace pro soustružení"
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "operation_group": {
                        "type": "string",
                        "description": "Filtr podle skupiny operací"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 50
                    }
                }
            }
        ),
        
        # STROJE
        Tool(
            name="get_machines",
            description="""
            Seznam strojů a jejich aktuální stav.
            Použití: "Které stroje jsou volné?" nebo "Jaký je stav stroje XYZ?"
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "status_filter": {
                        "type": "string",
                        "description": "Filtr podle stavu stroje"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 50
                    }
                }
            }
        ),
        
        # STATISTIKY
        Tool(
            name="get_production_stats",
            description="""
            Statistiky výroby za období.
            Použití: "Jaká je produktivita tento měsíc?" nebo "Zobraz statistiky výroby"
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "date_from": {
                        "type": "string",
                        "description": "Datum od"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "Datum do"
                    }
                },
                "required": ["date_from", "date_to"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Zpracování volání tools"""
    try:
        logger.info(f"Tool called: {name} with args: {arguments}")
        
        # Zpracování podle typu tool
        if name == "get_orders":
            result = await db.get_orders(**arguments)
            anonymized = anonymizer.anonymize_orders(result)
            response = response_builder.build_orders_response(anonymized, arguments)
            
        elif name == "get_order_detail":
            result = await db.get_order_detail(**arguments)
            anonymized = anonymizer.anonymize_order_detail(result)
            response = response_builder.build_order_detail_response(anonymized)
            
        elif name == "search_orders":
            result = await db.search_orders(**arguments)
            anonymized = anonymizer.anonymize_orders(result)
            response = response_builder.build_search_response(anonymized, arguments)
            
        elif name == "get_workers":
            result = await db.get_workers(**arguments)
            anonymized = anonymizer.anonymize_workers(result)
            response = response_builder.build_workers_response(anonymized, arguments)
            
        elif name == "get_worker_detail":
            result = await db.get_worker_detail(**arguments)
            anonymized = anonymizer.anonymize_worker_detail(result)
            response = response_builder.build_worker_detail_response(anonymized)
            
        elif name == "get_materials":
            result = await db.get_materials(**arguments)
            response = response_builder.build_materials_response(result, arguments)
            
        elif name == "get_material_movements":
            result = await db.get_material_movements(**arguments)
            response = response_builder.build_movements_response(result, arguments)
            
        elif name == "get_operations":
            result = await db.get_operations(**arguments)
            response = response_builder.build_operations_response(result, arguments)
            
        elif name == "get_machines":
            result = await db.get_machines(**arguments)
            response = response_builder.build_machines_response(result, arguments)
            
        elif name == "get_production_stats":
            result = await db.get_production_stats(**arguments)
            response = response_builder.build_stats_response(result, arguments)
            
        else:
            response = {
                "status": "error",
                "message": f"Neznámý tool: {name}"
            }
        
        # Vrácení odpovědi jako JSON text
        return [TextContent(
            type="text",
            text=json.dumps(response, ensure_ascii=False, indent=2)
        )]
        
    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}", exc_info=True)
        error_response = {
            "status": "error",
            "message": f"Chyba při zpracování: {str(e)}",
            "action": {
                "type": "show_message",
                "message": "Došlo k chybě při načítání dat"
            }
        }
        return [TextContent(
            type="text",
            text=json.dumps(error_response, ensure_ascii=False, indent=2)
        )]


async def main():
    """Hlavní funkce serveru"""
    await initialize()
    
    # Import stdio transportu
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        logger.info("Server starting...")
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
