"""
Data Anonymizer pro eMISTR MCP Server
Zajišťuje anonymizaci citlivých osobních údajů v odpovědích
"""

import re
import hashlib
from typing import Dict, List, Any


class DataAnonymizer:
    """Anonymizátor osobních a citlivých dat"""
    
    def __init__(self, config):
        self.config = config
        self.enabled = config.anonymization.get('enabled', True)
        self.preserve_ids = config.anonymization.get('preserve_ids', True)
        
        # Cache pro konzistentní anonymizaci
        self._customer_cache = {}
        self._worker_cache = {}
    
    def _generate_anonymous_id(self, original: str, prefix: str) -> str:
        """Generuje konzistentní anonymní ID z originálu"""
        hash_obj = hashlib.md5(str(original).encode())
        hash_hex = hash_obj.hexdigest()[:6].upper()
        return f"{prefix}_{hash_hex}"
    
    def _anonymize_customer_name(self, name: str, customer_id: int) -> str:
        """Anonymizace jména zákazníka"""
        if not self.enabled or not name:
            return name
        
        if customer_id not in self._customer_cache:
            self._customer_cache[customer_id] = self._generate_anonymous_id(
                f"customer_{customer_id}", "ZÁKAZNÍK"
            )
        
        return self._customer_cache[customer_id]
    
    def _anonymize_worker_name(self, name: str, worker_id: int) -> str:
        """Anonymizace jména zaměstnance"""
        if not self.enabled or not name:
            return name
        
        if worker_id not in self._worker_cache:
            self._worker_cache[worker_id] = self._generate_anonymous_id(
                f"worker_{worker_id}", "ZAMĚSTNANEC"
            )
        
        return self._worker_cache[worker_id]
    
    def _anonymize_email(self, email: str) -> str:
        """Anonymizace emailové adresy"""
        if not self.enabled or not email:
            return email
        
        if '@' in email:
            local, domain = email.split('@', 1)
            return f"email_***@***"
        return "email_***"
    
    def _anonymize_phone(self, phone: str) -> str:
        """Anonymizace telefonního čísla"""
        if not self.enabled or not phone:
            return phone
        
        # Zachová formát, ale skryje čísla
        cleaned = re.sub(r'\d', 'X', phone)
        return cleaned
    
    def _anonymize_note(self, note: str) -> str:
        """Anonymizace poznámek - odstraní potenciálně citlivé informace"""
        if not self.enabled or not note:
            return note
        
        # Odstranění emailů
        note = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                     '[email]', note)
        
        # Odstranění telefonních čísel
        note = re.sub(r'\+?\d[\d\s\-\(\)]{7,}\d', '[telefon]', note)
        
        # Odstranění IČO/DIČ
        note = re.sub(r'\b\d{8}\b', '[IČO]', note)
        
        return note
    
    # ==================== ZAKÁZKY ====================
    
    def anonymize_orders(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymizace seznamu zakázek"""
        if not self.enabled:
            return data
        
        anonymized_orders = []
        for order in data.get('orders', []):
            anonymized_order = order.copy()
            
            # Anonymizace jména zákazníka
            if 'customer_name' in anonymized_order:
                customer_id = anonymized_order.get('customer_id', 0)
                anonymized_order['customer_name'] = self._anonymize_customer_name(
                    anonymized_order['customer_name'], customer_id
                )
            
            # Anonymizace poznámek
            if 'note' in anonymized_order:
                anonymized_order['note'] = self._anonymize_note(anonymized_order['note'])
            
            anonymized_orders.append(anonymized_order)
        
        return {
            'orders': anonymized_orders,
            'stats': data.get('stats', {})
        }
    
    def anonymize_order_detail(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymizace detailu zakázky"""
        if not self.enabled:
            return data
        
        result = data.copy()
        
        # Anonymizace hlavičky zakázky
        if 'order' in result:
            order = result['order'].copy()
            
            if 'customer_name' in order:
                customer_id = order.get('customer_id', 0)
                order['customer_name'] = self._anonymize_customer_name(
                    order['customer_name'], customer_id
                )
            
            if 'customer_full_name' in order:
                customer_id = order.get('customer_id', 0)
                order['customer_full_name'] = self._anonymize_customer_name(
                    order['customer_full_name'], customer_id
                )
            
            if 'note' in order:
                order['note'] = self._anonymize_note(order['note'])
            
            if 'note2' in order:
                order['note2'] = self._anonymize_note(order['note2'])
            
            # Odstranění IČO/DIČ zákazníka
            if 'ico' in order:
                order['ico'] = '********'
            if 'dic' in order:
                order['dic'] = '**********'
            
            result['order'] = order
        
        # Anonymizace komentářů u operací
        if 'operations' in result:
            anonymized_ops = []
            for op in result['operations']:
                op_copy = op.copy()
                if 'comment' in op_copy:
                    op_copy['comment'] = self._anonymize_note(op_copy['comment'])
                anonymized_ops.append(op_copy)
            result['operations'] = anonymized_ops
        
        return result
    
    # ==================== ZAMĚSTNANCI ====================
    
    def anonymize_workers(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymizace seznamu zaměstnanců"""
        if not self.enabled:
            return data
        
        anonymized_workers = []
        for worker in data.get('workers', []):
            anonymized_worker = worker.copy()
            
            # Anonymizace jména
            worker_id = anonymized_worker.get('id', 0)
            if 'name' in anonymized_worker:
                anonymized_worker['name'] = self._anonymize_worker_name(
                    anonymized_worker['name'], worker_id
                )
            
            if 'firstname' in anonymized_worker:
                anonymized_worker['firstname'] = 'XXX'
            
            if 'lastname' in anonymized_worker:
                anonymized_worker['lastname'] = 'XXX'
            
            # Anonymizace kontaktů
            if 'email' in anonymized_worker:
                anonymized_worker['email'] = self._anonymize_email(anonymized_worker['email'])
            
            if 'telefon' in anonymized_worker:
                anonymized_worker['telefon'] = self._anonymize_phone(anonymized_worker['telefon'])
            
            anonymized_workers.append(anonymized_worker)
        
        return {
            'workers': anonymized_workers,
            'count': data.get('count', 0)
        }
    
    def anonymize_worker_detail(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymizace detailu zaměstnance"""
        if not self.enabled:
            return data
        
        result = data.copy()
        
        if 'worker' in result:
            worker = result['worker'].copy()
            worker_id = worker.get('id', 0)
            
            # Anonymizace jména
            if 'name' in worker:
                worker['name'] = self._anonymize_worker_name(worker['name'], worker_id)
            
            if 'firstname' in worker:
                worker['firstname'] = 'XXX'
            
            if 'lastname' in worker:
                worker['lastname'] = 'XXX'
            
            # Anonymizace kontaktů
            if 'email' in worker:
                worker['email'] = self._anonymize_email(worker['email'])
            
            if 'telefon' in worker:
                worker['telefon'] = self._anonymize_phone(worker['telefon'])
            
            # Anonymizace poznámek
            if 'comment' in worker:
                worker['comment'] = self._anonymize_note(worker['comment'])
            
            # Odstranění osobních údajů
            if 'birthdate' in worker:
                worker['birthdate'] = None
            
            if 'card' in worker:
                worker['card'] = '****'
            
            if 'card_dmr' in worker:
                worker['card_dmr'] = '****'
            
            result['worker'] = worker
        
        return result
    
    # ==================== UTILITY ====================
    
    def get_anonymization_mapping(self) -> Dict[str, Any]:
        """Vrátí mapování anonymizovaných hodnot (pro debugging)"""
        return {
            'customers': {v: k for k, v in self._customer_cache.items()},
            'workers': {v: k for k, v in self._worker_cache.items()}
        }
    
    def clear_cache(self):
        """Vymazání cache anonymizace"""
        self._customer_cache.clear()
        self._worker_cache.clear()
