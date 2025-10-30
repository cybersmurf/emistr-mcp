"""
Configuration Manager pro eMISTR MCP Server
"""

import json
import os
from typing import Dict, Any


class Config:
    """Správce konfigurace serveru"""
    
    def __init__(self, config_path: str = None):
        # Pokus o načtení konfigurace z environment variable
        if config_path is None:
            config_path = os.environ.get('EMISTR_CONFIG', 'config.json')
        
        self.config_path = config_path
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Načte konfiguraci ze souboru"""
        if not os.path.exists(self.config_path):
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Chyba při načítání konfigurace: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Vrátí výchozí konfiguraci"""
        return {
            "database": {
                "host": "localhost",
                "port": 3306,
                "database": "sud_utf8_aaa",
                "user": "root",
                "password": ""
            },
            "anonymization": {
                "enabled": True,
                "preserve_ids": True
            },
            "logging": {
                "level": "INFO",
                "file": "emistr_mcp.log"
            },
            "limits": {
                "max_query_results": 1000,
                "default_page_size": 50
            }
        }
    
    @property
    def database(self) -> Dict[str, Any]:
        """Databázová konfigurace"""
        return self._config.get('database', {})
    
    @property
    def anonymization(self) -> Dict[str, Any]:
        """Nastavení anonymizace"""
        return self._config.get('anonymization', {})
    
    @property
    def logging(self) -> Dict[str, Any]:
        """Nastavení logování"""
        return self._config.get('logging', {})
    
    @property
    def limits(self) -> Dict[str, Any]:
        """Limity dotazů"""
        return self._config.get('limits', {})
    
    def save(self, path: str = None):
        """Uloží konfiguraci do souboru"""
        save_path = path or self.config_path
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Získá hodnotu z konfigurace"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """Nastaví hodnotu v konfiguraci"""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
