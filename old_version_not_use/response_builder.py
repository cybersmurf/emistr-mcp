"""
Response Builder pro eMISTR MCP Server
Vytváří strukturované odpovědi s akcemi pro Delphi aplikaci
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


class ResponseBuilder:
    """Builder pro unifikované odpovědi"""
    
    def __init__(self):
        pass
    
    def _create_base_response(self, status: str = "success") -> Dict[str, Any]:
        """Vytvoří základní strukturu odpovědi"""
        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "action": {},
            "data": {},
            "message": ""
        }
    
    # ==================== ZAKÁZKY ====================
    
    def build_orders_response(self, data: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Odpověď pro seznam zakázek"""
        response = self._create_base_response()
        
        orders = data.get('orders', [])
        stats = data.get('stats', {})
        
        # Akce pro Delphi
        response['action'] = {
            'type': 'open_window',
            'window': 'order_list',
            'filters': filters
        }
        
        # Data
        response['data'] = {
            'items': orders,
            'summary': {
                'total_count': len(orders),
                'active_count': stats.get('active_count', 0),
                'delayed_count': stats.get('delayed_count', 0),
                'displayed_count': len(orders)
            },
            'metadata': {
                'filters_applied': filters,
                'columns': [
                    {'key': 'code', 'label': 'Kód zakázky', 'type': 'string'},
                    {'key': 'name', 'label': 'Název', 'type': 'string'},
                    {'key': 'customer_name', 'label': 'Zákazník', 'type': 'string'},
                    {'key': 'start', 'label': 'Zahájení', 'type': 'date'},
                    {'key': 'finish', 'label': 'Ukončení', 'type': 'date'},
                    {'key': 'kusu', 'label': 'Kusů', 'type': 'decimal'},
                    {'key': 'prevedeno', 'label': 'Převedeno', 'type': 'decimal'},
                    {'key': 'active', 'label': 'Stav', 'type': 'string'},
                    {'key': 'priorita', 'label': 'Priorita', 'type': 'integer'}
                ]
            }
        }
        
        # Zpráva
        delayed_msg = f", {stats.get('delayed_count', 0)} zpožděno" if stats.get('delayed_count', 0) > 0 else ""
        response['message'] = f"Nalezeno {len(orders)} zakázek{delayed_msg}"
        
        return response
    
    def build_order_detail_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Odpověď pro detail zakázky"""
        response = self._create_base_response()
        
        if 'error' in data:
            response['status'] = 'error'
            response['message'] = data['error']
            response['action'] = {
                'type': 'show_message',
                'message': data['error']
            }
            return response
        
        order = data.get('order', {})
        operations = data.get('operations', [])
        materials = data.get('materials', [])
        
        # Výpočet dokončení
        total_time = float(order.get('user_time', 0))
        real_time = float(order.get('real_time', 0))
        completion = (real_time / total_time * 100) if total_time > 0 else 0
        
        # Akce
        response['action'] = {
            'type': 'show_detail',
            'window': 'order_detail',
            'item_id': order.get('id'),
            'tabs': ['header', 'operations', 'materials', 'documents']
        }
        
        # Data
        response['data'] = {
            'order': order,
            'operations': operations,
            'materials': materials,
            'summary': {
                'completion_percent': round(completion, 2),
                'operations_count': len(operations),
                'operations_completed': sum(1 for op in operations if float(op.get('vyrobenocelkem', 0)) >= float(op.get('units', 0))),
                'materials_count': len(materials),
                'total_hours_planned': total_time,
                'total_hours_actual': real_time,
                'efficiency_percent': round((total_time / real_time * 100) if real_time > 0 else 0, 2)
            }
        }
        
        response['message'] = f"Detail zakázky {order.get('code')} - {order.get('name')}"
        
        return response
    
    def build_search_response(self, data: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Odpověď pro vyhledávání"""
        response = self._create_base_response()
        
        orders = data.get('orders', [])
        search_term = filters.get('search_term', '')
        
        response['action'] = {
            'type': 'open_window',
            'window': 'search_results',
            'search_term': search_term
        }
        
        response['data'] = {
            'items': orders,
            'summary': {
                'results_count': len(orders),
                'search_term': search_term
            }
        }
        
        response['message'] = f"Nalezeno {len(orders)} zakázek pro hledaný výraz '{search_term}'"
        
        return response
    
    # ==================== ZAMĚSTNANCI ====================
    
    def build_workers_response(self, data: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Odpověď pro seznam zaměstnanců"""
        response = self._create_base_response()
        
        workers = data.get('workers', [])
        
        response['action'] = {
            'type': 'open_window',
            'window': 'worker_list',
            'filters': filters
        }
        
        response['data'] = {
            'items': workers,
            'summary': {
                'total_count': len(workers),
                'active_count': sum(1 for w in workers if w.get('active') == 'ANO')
            },
            'metadata': {
                'columns': [
                    {'key': 'bar_id', 'label': 'Kód', 'type': 'string'},
                    {'key': 'name', 'label': 'Jméno', 'type': 'string'},
                    {'key': 'group_name', 'label': 'Skupina', 'type': 'string'},
                    {'key': 'profese', 'label': 'Profese', 'type': 'string'},
                    {'key': 'misto_prace', 'label': 'Místo práce', 'type': 'string'},
                    {'key': 'active', 'label': 'Aktivní', 'type': 'string'}
                ]
            }
        }
        
        response['message'] = f"Nalezeno {len(workers)} zaměstnanců"
        
        return response
    
    def build_worker_detail_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Odpověď pro detail zaměstnance"""
        response = self._create_base_response()
        
        if 'error' in data:
            response['status'] = 'error'
            response['message'] = data['error']
            return response
        
        worker = data.get('worker', {})
        stats = data.get('stats', {})
        
        response['action'] = {
            'type': 'show_detail',
            'window': 'worker_detail',
            'item_id': worker.get('id')
        }
        
        response['data'] = {
            'worker': worker,
            'stats': stats,
            'summary': {
                'orders_last_30_days': stats.get('orders_count', 0),
                'total_hours_last_30_days': stats.get('total_hours', 0),
                'avg_hours_per_order': round(float(stats.get('avg_hours_per_order', 0)), 2),
                'last_work_date': stats.get('last_work_date')
            }
        }
        
        response['message'] = f"Detail zaměstnance {worker.get('bar_id')}"
        
        return response
    
    # ==================== MATERIÁL ====================
    
    def build_materials_response(self, data: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Odpověď pro seznam materiálů"""
        response = self._create_base_response()
        
        materials = data.get('materials', [])
        
        # Identifikace materiálů s nízkou zásobou
        low_stock = [m for m in materials if float(m.get('stock_quantity', 0)) < float(m.get('min_quantity', 0))]
        
        response['action'] = {
            'type': 'open_window',
            'window': 'material_list',
            'filters': filters,
            'highlight_low_stock': True if low_stock else False
        }
        
        response['data'] = {
            'items': materials,
            'summary': {
                'total_count': len(materials),
                'low_stock_count': len(low_stock),
                'total_value': sum(float(m.get('stock_quantity', 0)) * float(m.get('cena_nakup', 0)) for m in materials)
            },
            'metadata': {
                'columns': [
                    {'key': 'bar_id', 'label': 'Kód', 'type': 'string'},
                    {'key': 'name', 'label': 'Název', 'type': 'string'},
                    {'key': 'stock_quantity', 'label': 'Množství', 'type': 'decimal'},
                    {'key': 'min_quantity', 'label': 'Min. množství', 'type': 'decimal'},
                    {'key': 'jednotka', 'label': 'Jednotka', 'type': 'string'},
                    {'key': 'warehouse_name', 'label': 'Sklad', 'type': 'string'}
                ]
            }
        }
        
        if low_stock:
            response['message'] = f"Nalezeno {len(materials)} materiálů, {len(low_stock)} pod minimální zásobou"
        else:
            response['message'] = f"Nalezeno {len(materials)} materiálů"
        
        return response
    
    def build_movements_response(self, data: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Odpověď pro pohyby materiálu"""
        response = self._create_base_response()
        
        movements = data.get('movements', [])
        
        response['action'] = {
            'type': 'open_window',
            'window': 'material_movements',
            'filters': filters
        }
        
        response['data'] = {
            'items': movements,
            'summary': {
                'movements_count': len(movements),
                'total_in': sum(float(m.get('mnozstvi', 0)) for m in movements if m.get('typ_pohybu') == 'P'),
                'total_out': sum(float(m.get('mnozstvi', 0)) for m in movements if m.get('typ_pohybu') == 'V')
            }
        }
        
        response['message'] = f"Nalezeno {len(movements)} pohybů materiálu"
        
        return response
    
    # ==================== OPERACE ====================
    
    def build_operations_response(self, data: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Odpověď pro seznam operací"""
        response = self._create_base_response()
        
        operations = data.get('operations', [])
        
        response['action'] = {
            'type': 'open_window',
            'window': 'operation_list',
            'filters': filters
        }
        
        response['data'] = {
            'items': operations,
            'summary': {
                'total_count': len(operations)
            }
        }
        
        response['message'] = f"Nalezeno {len(operations)} operací"
        
        return response
    
    # ==================== STROJE ====================
    
    def build_machines_response(self, data: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Odpověď pro seznam strojů"""
        response = self._create_base_response()
        
        machines = data.get('machines', [])
        
        # Statistiky stavů
        busy_count = sum(1 for m in machines if m.get('current_status') == 'busy')
        idle_count = sum(1 for m in machines if m.get('current_status') == 'idle')
        
        response['action'] = {
            'type': 'open_window',
            'window': 'machine_list',
            'filters': filters
        }
        
        response['data'] = {
            'items': machines,
            'summary': {
                'total_count': len(machines),
                'busy_count': busy_count,
                'idle_count': idle_count
            }
        }
        
        response['message'] = f"Nalezeno {len(machines)} strojů ({busy_count} v provozu, {idle_count} nečinných)"
        
        return response
    
    # ==================== STATISTIKY ====================
    
    def build_stats_response(self, data: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Odpověď pro statistiky výroby"""
        response = self._create_base_response()
        
        daily_stats = data.get('daily_stats', [])
        top_operations = data.get('top_operations', [])
        period = data.get('period', {})
        
        total_hours = sum(float(d.get('total_hours', 0)) for d in daily_stats)
        avg_workers = sum(int(d.get('workers_count', 0)) for d in daily_stats) / len(daily_stats) if daily_stats else 0
        
        response['action'] = {
            'type': 'open_window',
            'window': 'production_stats',
            'period': period
        }
        
        response['data'] = {
            'daily_stats': daily_stats,
            'top_operations': top_operations,
            'summary': {
                'total_hours': round(total_hours, 2),
                'average_workers_per_day': round(avg_workers, 1),
                'days_count': len(daily_stats),
                'average_hours_per_day': round(total_hours / len(daily_stats), 2) if daily_stats else 0
            },
            'period': period
        }
        
        response['message'] = f"Statistiky výroby za období {period.get('from')} - {period.get('to')}"
        
        return response
