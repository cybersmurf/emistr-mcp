# Changelog

Všechny významné změny v tomto projektu budou dokumentovány v tomto souboru.

Formát vychází z [Keep a Changelog](https://keepachangelog.com/cs/1.0.0/),
a projekt se řídí [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-10-29

### Přidáno
- Inicializace projektu eMISTR MCP Server
- Podpora pro MariaDB databázi (sud_utf8_aaa)
- MCP protokol implementace přes stdio
- Kompletní sada tools pro práci s eMISTR daty:
  - `get_orders` - Seznam zakázek s filtrováním
  - `get_order_detail` - Detail zakázky včetně operací
  - `search_orders` - Fulltextové vyhledávání
  - `get_workers` - Seznam zaměstnanců
  - `get_worker_detail` - Detail zaměstnance se statistikami
  - `get_materials` - Seznam materiálů na skladu
  - `get_material_movements` - Pohyby materiálu
  - `get_operations` - Seznam operací
  - `get_machines` - Seznam strojů
  - `get_production_stats` - Statistiky výroby

### Bezpečnost
- Automatická anonymizace osobních údajů (GDPR compliance)
- Read-only přístup k databázi
- Parametrizované SQL dotazy (ochrana proti SQL injection)
- Konfigurace hesel oddělena od kódu

### Dokumentace
- README.md - Hlavní dokumentace projektu
- QUICKSTART.md - Rychlý start za 5 minut
- INSTALL.md - Detailní instalační průvodce
- EXAMPLES.md - Příklady použití a dotazů
- DELPHI_INTEGRATION.md - Integrace s Delphi aplikací
- ARCHITECTURE.md - Architektura a struktura projektu

### Nástroje
- test_server.py - Testovací suite
- config.example.json - Ukázková konfigurace
- requirements.txt - Python závislosti

## [Unreleased]

### Přidáno
- CI workflow (GitHub Actions) pro testy/lint
- Issue templates (bug, feature)

### Změněno
- `get_machines`: dotaz upraven dle schématu (`stroje` + `stroj_group`), odstraněna závislost na stavech
- `get_production_stats`: výpočet hodin pomocí `TIMESTAMPDIFF(SECOND, start, finish)/3600.0`, filtrování podle `rd.start`
- `get_materials`: pole sjednocena dle `sklad_material`, `IFNULL` pro numerické hodnoty
- `get_orders`: přidán parametr `columns` pro filtrování polí; `active` vracen jako integer
- Dokumentace: README/ARCHITECTURE/INSTALL/OVERVIEW/EXAMPLES/DELIVERY/INDEX aktualizovány

### Plánováno
- Cache layer pro rychlejší odpovědi
- Podpora pro více databází současně
- Webhooks pro real-time notifikace
- Export dat do Excel/PDF
- Automatické reporty
- Dashboard s metrikami
- Podpora pro GraphQL
- REST API endpoint (alternativa k MCP)

---

## Typy změn

- **Přidáno** - pro nové funkce
- **Změněno** - pro změny v existujících funkcích
- **Zastaralé** - pro funkce, které budou brzy odstraněny
- **Odstraněno** - pro nyní odstraněné funkce
- **Opraveno** - pro opravy chyb
- **Bezpečnost** - v případě zranitelností
