"""
Database Manager pro eMISTR MCP Server
Zajišťuje bezpečný přístup k databázi s parametrizovanými dotazy
"""

import asyncio
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import aiomysql
import logging
from decimal import Decimal

logger = logging.getLogger('emistr-mcp.database')


class DatabaseManager:
    """Správce databázových připojení a dotazů"""
    
    def __init__(self, config):
        self.config = config
        self.pool = None
    
    async def connect(self):
        """Vytvoření connection poolu"""
        db_config = self.config.database
        self.pool = await aiomysql.create_pool(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            db=db_config['database'],
            charset='utf8mb4',
            autocommit=True,
            minsize=1,
            maxsize=10
        )
        logger.info("Database connection pool created")
    
    async def close(self):
        """Uzavření connection poolu"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()

    async def disconnect(self):
        """Backward-compatible alias for closing the pool (used by server cleanup)."""
        await self.close()
    
    async def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Spuštění SELECT dotazu"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, params or ())
                result = await cursor.fetchall()
                # Konverze datetime a decimal objektů na serializovatelné
                return [self._serialize_row(row) for row in result]
    
    def _serialize_row(self, row: Dict) -> Dict:
        """Konverze datových typů pro JSON serializaci"""
        serialized = {}
        for key, value in row.items():
            if isinstance(value, (datetime, date)):
                serialized[key] = value.isoformat()
            elif isinstance(value, Decimal):
                serialized[key] = float(value)  # Convert Decimal to float
            elif isinstance(value, bytes):
                serialized[key] = value.decode('utf-8', errors='ignore')
            else:
                serialized[key] = value
        return serialized

    async def _detect_datetime_column(self, table_name: str) -> Optional[str]:
        """Najde název sloupce typu datetime/timestamp/date v dané tabulce (preferuje známé názvy)."""
        try:
            db_name = self.config.database.get('database') if isinstance(self.config.database, dict) else None
            if not db_name:
                return None
            rows = await self.execute_query(
                """
                SELECT COLUMN_NAME, DATA_TYPE
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                  AND DATA_TYPE IN ('datetime','timestamp','date')
                """,
                (db_name, table_name)
            )
            preferred = ['datum', 'date', 'datumcas', 'datetime', 'ts', 'timestamp']
            # Prefer known names
            for name in preferred:
                if any(r.get('COLUMN_NAME') == name for r in rows):
                    return name
            # Otherwise pick the first available
            if rows:
                name = rows[0].get('COLUMN_NAME')
                # basic safety
                if isinstance(name, str) and name.replace('_', '').isalnum():
                    return name
            return None
        except Exception:
            return None

    async def _existing_columns(self, table_name: str, candidates: List[str]) -> List[str]:
        """Vrátí existující sloupce z candidates v dané tabulce (přes information_schema; fallback SHOW COLUMNS)."""
        try:
            db_name = self.config.database.get('database') if isinstance(self.config.database, dict) else None
            if db_name:
                rows = await self.execute_query(
                    """
                    SELECT COLUMN_NAME
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                    """,
                    (db_name, table_name)
                )
                names = {r.get('COLUMN_NAME') for r in rows}
                return [c for c in candidates if c in names]
        except Exception:
            pass
        # Fallback SHOW COLUMNS
        try:
            rows = await self.execute_query(f"SHOW COLUMNS FROM {table_name}")
            names = {r.get('Field') or r.get('COLUMN_NAME') for r in rows}
            return [c for c in candidates if c in names]
        except Exception:
            return []
    
    # ==================== ZAKÁZKY ====================
    
    async def get_orders(
        self,
        status: str = "",
        customer_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Získání seznamu zakázek"""
        
        query = """
            SELECT 
                o.id,
                o.bar_id,
                o.code,
                o.name,
                CAST(o.active AS SIGNED) as active,
                o.start,
                o.finish,
                o.customer_id,
                o.customer_name,
                o.kusu,
                o.prevedeno,
                o.user_time,
                o.real_time,
                o.user_price,
                o.real_price,
                o.priorita,
                o.datumExpedice,
                o.note,
                os.name as status_name
            FROM c_order o
            LEFT JOIN order_stav os ON o.active = os.id
            WHERE 1=1
        """
        
        params = []
        
        if status:
            query += " AND o.active = %s"
            params.append(status)
        
        if customer_id:
            query += " AND o.customer_id = %s"
            params.append(customer_id)
        
        if date_from:
            query += " AND o.start >= %s"
            params.append(date_from)
        
        if date_to:
            query += " AND o.finish <= %s"
            params.append(date_to)
        
        query += " ORDER BY o.priorita DESC, o.start ASC LIMIT %s OFFSET %s"
        params.append(limit)
        params.append(offset)
        
        orders = await self.execute_query(query, tuple(params))
        
        # Statistiky
        stats_query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN active = 'ANO' THEN 1 ELSE 0 END) as active_count,
                SUM(CASE WHEN finish < CURDATE() AND active = 'ANO' THEN 1 ELSE 0 END) as delayed_count
            FROM c_order
            WHERE 1=1
        """
        
        stats_params = []
        if customer_id:
            stats_query += " AND customer_id = %s"
            stats_params.append(customer_id)
        
        stats = await self.execute_query(stats_query, tuple(stats_params))
        
        return {
            "orders": orders,
            "stats": stats[0] if stats else {}
        }
    
    async def get_order_detail(
        self,
        order_id: Optional[int] = None,
        order_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Detail zakázky včetně operací"""
        
        # Hlavička zakázky
        query = """
            SELECT 
                o.*,
                os.name as status_name,
                c.name as customer_full_name,
                c.ico,
                c.dic
            FROM c_order o
            LEFT JOIN order_stav os ON o.active = os.name
            LEFT JOIN customer c ON o.customer_id = c.id
            WHERE 
        """
        
        if order_id:
            query += "o.id = %s"
            params = (order_id,)
        elif order_code:
            query += "o.code = %s"
            params = (order_code,)
        else:
            return {"error": "Musíte zadat order_id nebo order_code"}
        
        order = await self.execute_query(query, params)
        if not order:
            return {"error": "Zakázka nenalezena"}
        
        order = order[0]
        
        # Operace zakázky
        operations_query = """
            SELECT 
                ow.id,
                ow.operation_id,
                op.name as operation_name,
                op.bar_id as operation_code,
                ow.user_time,
                ow.real_time,
                ow.odpracovano,
                ow.user_price,
                ow.real_price,
                ow.vyrobenocelkem,
                ow.units,
                ow.poradi,
                ow.start_req,
                ow.finish_req,
                ow.comment
            FROM order_work ow
            LEFT JOIN operation op ON ow.operation_id = op.id
            WHERE ow.order_id = %s
            ORDER BY ow.poradi
        """
        
        operations = await self.execute_query(operations_query, (str(order['id']),))
        
        # Materiál
        material_query = """
            SELECT 
                m.id,
                m.material_id,
                mat.name as material_name,
                m.mnozstvi,
                m.jednotka,
                m.vydano_mnozstvi,
                m.cena_nakup,
                m.cena_celkem
            FROM material m
            LEFT JOIN sklad_material mat ON m.material_id = mat.id
            WHERE m.order_id = %s
        """
        material_fallback = """
            SELECT 
                m.id,
                m.material_id,
                mat.name as material_name,
                m.mnozstvi,
                m.jednotka,
                0 as vydano_mnozstvi,
                m.cena_nakup,
                m.cena_celkem
            FROM material m
            LEFT JOIN sklad_material mat ON m.material_id = mat.id
            WHERE m.order_id = %s
        """
        material_fallback2 = """
            SELECT 
                m.id,
                m.material_id,
                mat.name as material_name,
                m.mnozstvi,
                m.jednotka,
                0 as vydano_mnozstvi,
                0 as cena_nakup,
                0 as cena_celkem
            FROM material m
            LEFT JOIN sklad_material mat ON m.material_id = mat.id
            WHERE m.order_id = %s
        """
        try:
            materials = await self.execute_query(material_query, (order['id'],))
        except Exception as e:
            if "Unknown column" in str(e):
                try:
                    materials = await self.execute_query(material_fallback, (order['id'],))
                except Exception as e2:
                    if "Unknown column" in str(e2):
                        materials = await self.execute_query(material_fallback2, (order['id'],))
                    else:
                        raise
            else:
                raise
        
        return {
            "order": order,
            "operations": operations,
            "materials": materials
        }
    
    async def search_orders(self, search_term: str, limit: int = 20) -> Dict[str, Any]:
        """Fulltextové vyhledávání zakázek"""
        
        query = """
            SELECT 
                o.id,
                o.code,
                o.name,
                o.customer_name,
                o.active,
                o.start,
                o.finish,
                o.note
            FROM c_order o
            WHERE 
                o.code LIKE %s OR
                o.name LIKE %s OR
                o.customer_name LIKE %s OR
                o.cislo_objednavky LIKE %s OR
                o.note LIKE %s
            ORDER BY o.start DESC
            LIMIT %s
        """
        
        search_pattern = f"%{search_term}%"
        params = (search_pattern, search_pattern, search_pattern, search_pattern, search_pattern, limit)
        
        orders = await self.execute_query(query, params)
        
        return {
            "orders": orders,
            "search_term": search_term,
            "count": len(orders)
        }
    
    # ==================== ZAMĚSTNANCI ====================
    
    async def get_workers(
        self,
        status: str = "",
        group_name: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Seznam zaměstnanců"""
        
        query = """
            SELECT 
                w.id,
                w.name,
                w.bar_id,
                w.firstname,
                w.lastname,
                w.active,
                w.group_name,
                w.profese,
                w.misto_prace,
                w.email,
                w.telefon,
                w.start,
                w.finish
            FROM worker w
            WHERE 1=1
        """
        
        params = []
        
        if status:
            query += " AND w.active = %s"
            params.append(status)
        
        if group_name:
            query += " AND w.group_name = %s"
            params.append(group_name)
        
        query += " ORDER BY w.name LIMIT %s"
        params.append(limit)
        
        workers = await self.execute_query(query, tuple(params))
        
        return {
            "workers": workers,
            "count": len(workers)
        }
    
    async def get_worker_detail(self, worker_id: int) -> Dict[str, Any]:
        """Detail zaměstnance včetně statistik"""
        
        # Základní info
        query = """
            SELECT 
                w.*,
                wg.name as group_full_name
            FROM worker w
            LEFT JOIN worker_group wg ON w.group_id = wg.id
            WHERE w.id = %s
        """
        
        worker = await self.execute_query(query, (worker_id,))
        if not worker:
            return {"error": "Zaměstnanec nenalezen"}
        
        worker = worker[0]
        
        # Statistiky odpracovaných hodin
        stats_query = """
            SELECT 
                COUNT(DISTINCT rd.order_id) as orders_count,
                SUM(rd.real_time) as total_hours,
                AVG(rd.real_time) as avg_hours_per_order,
                MAX(rd.datum) as last_work_date
            FROM readdata rd
            WHERE rd.worker_id = %s
            AND rd.datum >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """
        
        stats = await self.execute_query(stats_query, (worker_id,))
        
        return {
            "worker": worker,
            "stats": stats[0] if stats else {}
        }

    async def get_material_movements(
        self,
        material_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Pohyby materiálu"""
        query = """
            SELECT 
                smp.id,
                smp.material_id,
                sm.name as material_name,
                smp.mnozstvi,
                smp.datum,
                smp.typ_pohybu,
                smp.order_id,
                smp.sklad_id,
                smp.cena
            FROM sklad_material_pohyb smp
            LEFT JOIN sklad_material sm ON smp.material_id = sm.id
            WHERE 1=1
        """
        
        params = []
        
        if material_id:
            query += " AND smp.material_id = %s"
            params.append(material_id)
        
        if date_from:
            query += " AND smp.datum >= %s"
            params.append(date_from)
        
        if date_to:
            query += " AND smp.datum <= %s"
            params.append(date_to)
        
        query += " ORDER BY smp.datum DESC LIMIT %s"
        params.append(limit)
        
        movements = await self.execute_query(query, tuple(params))
        return {
            "movements": movements,
            "count": len(movements)
        }
    
    # ==================== OPERACE ====================
    
    async def get_operations(
        self,
        operation_group: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Seznam operací"""
        
        base_query = """
            SELECT 
                op.id,
                op.name,
                op.bar_id,
                op.user_price,
                op.user_time,
                op.group_name,
                og.name as group_full_name
            FROM operation op
            LEFT JOIN operation_group og ON op.group_name = og.name
            WHERE 1=1
        """
        fallback_query = """
            SELECT 
                op.id,
                op.name,
                op.bar_id,
                0 as user_price,
                0 as user_time,
                op.group_name,
                og.name as group_full_name
            FROM operation op
            LEFT JOIN operation_group og ON op.group_name = og.name
            WHERE 1=1
        """
        
        params = []
        
        if operation_group:
            base_query += " AND op.group_name = %s"
            fallback_query += " AND op.group_name = %s"
            params.append(operation_group)
        
        base_query += " ORDER BY op.name LIMIT %s"
        fallback_query += " ORDER BY op.name LIMIT %s"
        params.append(limit)
        
        try:
            operations = await self.execute_query(base_query, tuple(params))
        except Exception as e:
            if "Unknown column" in str(e):
                operations = await self.execute_query(fallback_query, tuple(params))
            else:
                raise
        
        return {
            "operations": operations,
            "count": len(operations)
        }
    
    async def get_materials(
        self,
        low_stock_only: bool = False,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Seznam materiálů na skladu (sklad_material)"""
        query = """
            SELECT 
                sm.id,
                sm.name,
                sm.bar_id,
                IFNULL(sm.count, 0) as stock_quantity,
                IFNULL(sm.limit_count, 0) as min_quantity,
                sm.unit as jednotka,
                IFNULL(sm.price, 0) as cena_nakup,
                sm.sklad_id as warehouse_id
            FROM sklad_material sm
            ORDER BY sm.name
            LIMIT %s
        """
        materials = await self.execute_query(query, (limit,))
        if low_stock_only:
            materials = [m for m in materials if float(m.get('stock_quantity', 0) or 0) < float(m.get('min_quantity', 0) or 0)]
        return {
            "materials": materials,
            "count": len(materials)
        }
    
    # ==================== STROJE ====================
    
    async def get_machines(
        self,
        status_filter: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Seznam strojů (podle schema: stroje + stroj_group)"""
        # status_filter není v aktuálním schématu podporován, ignorujeme ho
        query = """
            SELECT 
                s.id,
                s.name,
                s.group_id,
                sg.name AS group_name
            FROM stroje s
            LEFT JOIN stroj_group sg ON sg.id = s.group_id
            ORDER BY s.name
            LIMIT %s
        """
        machines = await self.execute_query(query, (limit,))
        return {
            "machines": machines,
            "count": len(machines)
        }
    
    # ==================== STATISTIKY ====================
    
    async def get_production_stats(
        self,
        date_from: str,
        date_to: str
    ) -> Dict[str, Any]:
        """Statistiky výroby"""
        
        # Podle schema má readdata sloupec 'start' a 'finish' (datetime). Použijeme 'start'.
        coalesce_expr = "rd.start"
        hours_query = f"""
            SELECT 
                DATE({coalesce_expr}) as date,
                SUM(TIMESTAMPDIFF(SECOND, rd.start, rd.finish)) / 3600.0 as total_hours,
                COUNT(DISTINCT rd.worker_id) as workers_count,
                COUNT(DISTINCT rd.order_id) as orders_count
            FROM readdata rd
            WHERE {coalesce_expr} BETWEEN %s AND %s
            GROUP BY DATE({coalesce_expr})
            ORDER BY date
        """
        hours = await self.execute_query(hours_query, (date_from, date_to))

        operations_query = f"""
            SELECT 
                op.name,
                COUNT(*) as count,
                SUM(TIMESTAMPDIFF(SECOND, rd.start, rd.finish)) / 3600.0 as total_hours
            FROM readdata rd
            LEFT JOIN operation op ON rd.operation_id = op.id
            WHERE {coalesce_expr} BETWEEN %s AND %s
            GROUP BY op.name
            ORDER BY total_hours DESC
            LIMIT 10
        """
        operations = await self.execute_query(operations_query, (date_from, date_to))
        
        return {
            "period": {
                "from": date_from,
                "to": date_to
            },
            "daily_stats": hours,
            "top_operations": operations
        }
