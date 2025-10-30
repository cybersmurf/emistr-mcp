# Struktura projektu eMISTR MCP

```
emistr-mcp/
│
├── server.py                    # Hlavní MCP server s tool definicemi
├── database.py                  # Databázové dotazy a connection pool
├── anonymizer.py                # Anonymizace citlivých dat
├── response_builder.py          # Konstrukce unifikovaných odpovědí
├── config.py                    # Správa konfigurace
│
├── test_server.py               # Testovací skripty
│
├── config.json                  # Produkční konfigurace (NESDÍLET!)
├── config.example.json          # Ukázková konfigurace
│
├── requirements.txt             # Python závislosti
├── .gitignore                   # Git ignore soubor
│
├── README.md                    # Hlavní dokumentace
├── QUICKSTART.md                # Rychlý start (5 minut)
├── INSTALL.md                   # Detailní instalační průvodce
├── EXAMPLES.md                  # Příklady použití a dotazů
├── DELPHI_INTEGRATION.md        # Integrace s Delphi aplikací
└── LICENSE                      # Licence

```

## Popis hlavních komponent

### `server.py`
Hlavní soubor MCP serveru. Obsahuje:
- Definice všech tools (get_orders, get_workers, atd.)
- MCP protokol handler
- Volání databázových dotazů
- Anonymizaci a formatování odpovědí

**Klíčové funkce:**
- `list_tools()` - Seznam dostupných tools
- `call_tool()` - Zpracování volání tools
- `initialize()` - Inicializace serveru

### `database.py`
Správce databázového připojení a dotazů.

**Klíčové třídy:**
- `DatabaseManager` - Connection pool a query executor

**Hlavní metody:**
- `get_orders()` - Načtení zakázek s filtry
- `get_order_detail()` - Detail zakázky
- `search_orders()` - Fulltextové vyhledávání
- `get_workers()` - Seznam zaměstnanců
- `get_materials()` - Seznam materiálů
- `get_production_stats()` - Statistiky výroby
- `get_machines()` - Seznam strojů

**Bezpečnost:**
- Pouze READ-ONLY dotazy
- Parametrizované queries (ochrana proti SQL injection)
- Connection pooling pro výkon

### `anonymizer.py`
Anonymizace citlivých osobních údajů.

**Klíčové třídy:**
- `DataAnonymizer` - Hlavní anonymizační třída

**Co anonymizuje:**
- Jména zákazníků → `ZÁKAZNÍK_XXXXX`
- Jména zaměstnanců → `ZAMĚSTNANEC_XXXXX`
- Emailové adresy → `email_***@***`
- Telefonní čísla → `+420 XXX XXX XXX`
- IČO/DIČ → `********`
- Poznámky s osobními údaji

**Zachovává:**
- Interní ID a čísla
- Technická data
- Business data (množství, ceny, časy)

### `response_builder.py`
Vytváří strukturované odpovědi pro Delphi aplikaci.

**Klíčové třídy:**
- `ResponseBuilder` - Konstruktor odpovědí

**Formát odpovědi:**
```json
{
  "status": "success",
  "timestamp": "2024-10-29T10:30:00",
  "action": {
    "type": "open_window",
    "window": "order_list",
    "filters": {...}
  },
  "data": {
    "items": [...],
    "summary": {...},
    "metadata": {...}
  },
  "message": "Nalezeno 15 zakázek"
}
```

**Typy akcí:**
- `open_window` - Otevřít okno
- `show_detail` - Zobrazit detail
- `apply_filter` - Aplikovat filtr
- `refresh_list` - Obnovit seznam
- `show_message` - Zobrazit zprávu

### `config.py`
Správce konfigurace serveru.

**Klíčové třídy:**
- `Config` - Configuration manager

**Načítá z:**
- `config.json` (primárně)
- Environment variable `EMISTR_CONFIG`
- Výchozí hodnoty (fallback)

**Konfigurace:**
- Databázové připojení
- Nastavení anonymizace
- Logování
- Limity dotazů

### `test_server.py`
Testovací skripty pro ověření funkčnosti.

**Testy:**
- Připojení k databázi
- Načtení zakázek
- Anonymizace dat
- Formát odpovědí
- Vyhledávání
- Načtení zaměstnanců a materiálů

## Datový tok

```
┌─────────────┐
│  Claude AI  │
│  (Uživatel) │
└──────┬──────┘
       │ Dotaz: "Zobraz aktivní zakázky"
       ↓
┌──────────────────┐
│   MCP Protocol   │ (stdio komunikace)
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│   server.py      │
│   call_tool()    │ Rozpozná intent → get_orders
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│  database.py     │
│  get_orders()    │ SELECT ... WHERE active='ANO'
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│ MariaDB          │
│ sud_utf8_aaa     │ Vrátí data z tabulky c_order
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│ anonymizer.py    │
│ anonymize()      │ Zákazník XYZ → ZÁKAZNÍK_A1B2C3
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│response_builder  │
│ build_response() │ Vytvoří strukturu s action + data
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│   JSON Response  │ {status, action, data, message}
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│  Claude AI       │ Zobrazí uživateli
└──────────────────┘
       │
       ↓ (volitelně)
┌──────────────────┐
│ Delphi App       │ Zpracuje JSON, otevře okno
└──────────────────┘
```

## Architektura rozhodnutí

### Proč async?
- Lepší výkon při více souběžných dotazech
- Non-blocking I/O pro databázové operace
- Připravenost pro škálování

### Proč anonymizace?
- GDPR compliance
- Ochrana citlivých dat při práci s AI
- Možnost sdílení logs bez rizika

### Proč unifikovaný formát?
- Snadná integrace s Delphi
- Konzistence napříč všemi odpověďmi
- Rozšiřitelnost pro nové akce

### Proč connection pooling?
- Znovupoužití připojení
- Rychlejší response time
- Méně zátěže na databázi

## Zabezpečení

### Vrstvy bezpečnosti:

1. **Read-only přístup**
   - Server může pouze číst (SELECT)
   - Žádné INSERT, UPDATE, DELETE

2. **Parametrizované dotazy**
   - Ochrana proti SQL injection
   - Všechny user inputs jsou escaped

3. **Anonymizace**
   - Automatická pro všechny osobní údaje
   - Konzistentní napříč sessions

4. **Logování**
   - Všechny dotazy jsou logovány
   - Audit trail pro compliance

5. **Konfigurace**
   - Hesla v config.json (nikdy ne v kódu)
   - config.json v .gitignore

## Výkon

### Optimalizace:

- **Connection pooling**: Až 10 současných připojení
- **Limitování výsledků**: Default 50, max 1000 záznamů
- **Indexy**: Využívá DB indexy (bar_id, code, customer_id)
- **Lazy loading**: Data se načítají pouze když jsou potřeba
- **Caching**: Anonymizační cache pro konzistenci

### Očekávaný výkon:

- Jednoduchý dotaz: < 100ms
- Složitý dotaz s JOINy: < 500ms
- Fulltextové vyhledávání: < 200ms
- Statistiky: < 1s

## Rozšíření

Pro přidání nového toolu:

1. Přidejte definici do `list_tools()` v `server.py`
2. Vytvořte databázový dotaz v `database.py`
3. Přidejte anonymizační logiku v `anonymizer.py` (pokud potřeba)
4. Vytvořte response builder v `response_builder.py`
5. Přidejte handler do `call_tool()` v `server.py`
6. Aktualizujte dokumentaci

## Verze a kompatibilita

- **Python**: 3.11+
- **MariaDB**: 10.x+
- **MCP Protocol**: 1.0+
- **Claude Desktop**: Latest

## Maintenance

### Pravidelná údržba:

- Kontrola logů (týdně)
- Aktualizace závislostí (měsíčně)
- Review anonymizačních pravidel (kvartálně)
- Backup konfigurace (průběžně)

### Monitoring:

- Sledovat velikost log souboru
- Kontrolovat chybové stavy
- Měřit response time
- Auditovat přístupy

## Roadmap

### Možná budoucí rozšíření:

- [ ] Podpora pro více databází současně
- [ ] Cache layer (Redis)
- [ ] Webhooks pro real-time notifikace
- [ ] GraphQL interface
- [ ] Pokročilé analytics
- [ ] Export do různých formátů (Excel, PDF)
- [ ] Automatické reporty
- [ ] Dashboard s metrikami
