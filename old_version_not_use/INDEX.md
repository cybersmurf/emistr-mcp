# Index souborů projektu eMISTR MCP

Tento dokument obsahuje přehled všech souborů v projektu a jejich účel.

## 📁 Hlavní soubory

### `server.py` ⭐
**Účel:** Hlavní MCP server  
**Obsah:**
- Definice všech tools (get_orders, get_workers, atd.)
- MCP protokol handler
- Inicializace serveru
- Volání databázových dotazů a zpracování odpovědí

**Klíčové funkce:**
- `list_tools()` - Seznam dostupných tools
- `call_tool()` - Zpracování volání tools
- `initialize()` - Inicializace serveru a připojení k DB

---

### `database.py` 🗄️
**Účel:** Správce databázového připojení a dotazů  
**Obsah:**
- Connection pooling (aiomysql)
- Všechny SQL dotazy
- Parametrizované queries pro bezpečnost

**Klíčové metody:**
- `get_orders()` - Zakázky s filtry
- `get_order_detail()` - Detail zakázky
- `search_orders()` - Vyhledávání
- `get_workers()` - Zaměstnanci
- `get_materials()` - Materiály
- `get_production_stats()` - Statistiky

---

### `anonymizer.py` 🔒
**Účel:** Anonymizace citlivých dat  
**Obsah:**
- GDPR compliance logika
- Anonymizační algoritmy
- Cache pro konzistenci

**Co anonymizuje:**
- Jména zákazníků → `ZÁKAZNÍK_XXXXX`
- Jména zaměstnanců → `ZAMĚSTNANEC_XXXXX`
- Email → `email_***@***`
- Telefon → `+420 XXX XXX XXX`
- IČO/DIČ → `********`

---

### `response_builder.py` 📤
**Účel:** Konstrukce unifikovaných odpovědí  
**Obsah:**
- Builder pattern pro responses
- Formátování pro Delphi aplikaci
- Vytváření action objektů

**Klíčové metody:**
- `build_orders_response()`
- `build_order_detail_response()`
- `build_workers_response()`
- `build_materials_response()`
- atd.

---

### `config.py` ⚙️
**Účel:** Správa konfigurace  
**Obsah:**
- Načítání z config.json
- Environment variables
- Výchozí hodnoty

**Konfigurace:**
- Database settings
- Anonymization settings
- Logging settings
- Query limits

---

### `test_server.py` 🧪
**Účel:** Testovací suite  
**Obsah:**
- Unit testy pro všechny komponenty
- Integration testy
- Validace formátu odpovědí

**Testy:**
- Připojení k databázi
- Načítání dat
- Anonymizace
- Response format

---

## 📋 Konfigurační soubory

### `config.example.json` 📝
**Účel:** Ukázková konfigurace  
**Použití:** Zkopírovat jako `config.json` a upravit

```json
{
  "database": {...},
  "anonymization": {...},
  "logging": {...}
}
```

### `requirements.txt` 📦
**Účel:** Python závislosti  
**Použití:** `pip install -r requirements.txt`

**Závislosti:**
- mcp >= 1.0.0
- aiomysql >= 0.2.0
- PyMySQL >= 1.1.0

### `.gitignore` 🚫
**Účel:** Git ignore pravidla  
**Ignoruje:**
- config.json (obsahuje hesla)
- *.log
- __pycache__/
- venv/

---

## 📚 Dokumentace

### `README.md` 📖
**Účel:** Hlavní dokumentace projektu  
**Obsah:**
- Přehled projektu
- Hlavní funkce
- Podporované operace
- Instalace (stručně)
- Příklady použití
- Architektura
- Integrace s Delphi

**Pro koho:** Všichni uživatelé

---

### `QUICKSTART.md` ⚡
**Účel:** Rychlý start za 5 minut  
**Obsah:**
- Minimální instalace
- Základní konfigurace
- První test
- Rychlé řešení problémů

**Pro koho:** Nové uživatele, kteří chtějí rychle vyzkoušet

---

### `INSTALL.md` 🔧
**Účel:** Detailní instalační průvodce  
**Obsah:**
- Příprava prostředí (Windows/Linux/Mac)
- Instalace závislostí
- Konfigurace databáze
- Nastavení Claude Desktop
- Testování
- Řešení problémů
- Pokročilá konfigurace
- Automatické spuštění

**Pro koho:** Administrátory, deployment

---

### `EXAMPLES.md` 💡
**Účel:** Příklady použití a dotazů  
**Obsah:**
- Základní dotazy na zakázky
- Dotazy na zaměstnance
- Dotazy na materiál
- Operace a stroje
- Statistiky
- Složité dotazy
- Use cases
- Tipy a best practices

**Pro koho:** End-users, testování

---

### `DELPHI_INTEGRATION.md` 🔗
**Účel:** Integrace s Delphi aplikací  
**Obsah:**
- Formát odpovědi
- Typy akcí
- Pascal/Delphi kód
- Parsování JSON
- Zpracování akcí
- Naplnění UI
- Příklady implementace

**Pro koho:** Delphi vývojáře

---

### `ARCHITECTURE.md` 🏗️
**Účel:** Architektura a design  
**Obsah:**
- Struktura projektu
- Popis komponent
- Datový tok
- Architektonická rozhodnutí
- Bezpečnost
- Výkon
- Rozšíření
- Maintenance

**Pro koho:** Vývojáře, architekty

---

### `OVERVIEW.md` 🎯
**Účel:** Kompletní přehled řešení  
**Obsah:**
- Co bylo vytvořeno
- Jak to funguje
- Technologie
- Bezpečnost
- Výkon
- Dokumentace
- Příklady
- Podpora

**Pro koho:** Management, overview pro všechny

---

### `CHANGELOG.md` 📅
**Účel:** Historie změn  
**Obsah:**
- Verze 1.0.0 - Initial release
- Plánované změny
- Roadmap

**Pro koho:** Všichni (tracking změn)

---

### `LICENSE` ⚖️
**Účel:** Licenční ujednání  
**Obsah:**
- Proprietární licence Agerit s.r.o.
- Omezení použití
- Copyright

**Pro koho:** Právní oddělení

---

## 📊 Přehled podle typu

### Python soubory (.py)
1. ✅ `server.py` - MCP server
2. ✅ `database.py` - DB management
3. ✅ `anonymizer.py` - Anonymizace
4. ✅ `response_builder.py` - Response builder
5. ✅ `config.py` - Configuration
6. ✅ `test_server.py` - Testy

**Celkem:** 6 Python souborů

### Dokumentace (.md)
1. ✅ `README.md` - Hlavní dokumentace
2. ✅ `QUICKSTART.md` - Rychlý start
3. ✅ `INSTALL.md` - Instalace
4. ✅ `EXAMPLES.md` - Příklady
5. ✅ `DELPHI_INTEGRATION.md` - Delphi
6. ✅ `ARCHITECTURE.md` - Architektura
7. ✅ `OVERVIEW.md` - Přehled
8. ✅ `CHANGELOG.md` - Historie

**Celkem:** 8 dokumentačních souborů

### Konfigurační soubory
1. ✅ `config.example.json` - Ukázková konfigurace
2. ✅ `requirements.txt` - Python závislosti
3. ✅ `.gitignore` - Git ignore
4. ✅ `LICENSE` - Licence

**Celkem:** 4 konfigurační soubory

## 📈 Celková statistika

- **Python kód:** 6 souborů (~2000 řádků)
- **Dokumentace:** 8 souborů (~3000 řádků)
- **Konfigurace:** 4 soubory
- **Celkem:** 18 souborů

## 🎯 Doporučené pořadí čtení

### Pro rychlé nasazení:
1. `QUICKSTART.md` - 5 minut
2. `config.example.json` - Konfigurace
3. První test

### Pro kompletní pochopení:
1. `OVERVIEW.md` - Celkový přehled
2. `README.md` - Hlavní dokumentace
3. `INSTALL.md` - Detailní instalace
4. `EXAMPLES.md` - Příklady použití
5. `DELPHI_INTEGRATION.md` - Integrace
6. `ARCHITECTURE.md` - Architektura

### Pro vývojáře:
1. `ARCHITECTURE.md` - Architektura
2. `server.py` - Hlavní kód
3. `database.py` - DB dotazy
4. `anonymizer.py` - Anonymizace
5. `response_builder.py` - Responses

## 🔍 Hledání informací

### "Jak nainstalovat?"
→ `INSTALL.md`

### "Jak používat?"
→ `EXAMPLES.md`

### "Jak integrovat s Delphi?"
→ `DELPHI_INTEGRATION.md`

### "Jak to funguje?"
→ `ARCHITECTURE.md`

### "Rychlý přehled?"
→ `OVERVIEW.md`

### "Rychlý start?"
→ `QUICKSTART.md`

### "Co je nového?"
→ `CHANGELOG.md`

## 📦 Před nasazením

### Checklist:

- [ ] Přečíst `QUICKSTART.md` nebo `INSTALL.md`
- [ ] Zkopírovat `config.example.json` → `config.json`
- [ ] Nastavit DB credentials v `config.json`
- [ ] Nainstalovat dependencies: `pip install -r requirements.txt`
- [ ] Spustit testy: `python test_server.py`
- [ ] Nakonfigurovat Claude Desktop
- [ ] Otestovat první dotaz

## 💾 Backup důležitých souborů

**VŽDY zálohujte:**
- ✅ `config.json` (obsahuje hesla!)
- ✅ `emistr_mcp.log` (audit trail)

**NIKDY nesdílejte:**
- ❌ `config.json` (obsahuje citlivá data)
- ❌ Log soubory (mohou obsahovat citlivé informace)

## 🔄 Aktualizace

Při aktualizaci projektu:

1. Zálohovat `config.json`
2. Stáhnout nové soubory
3. Zkontrolovat `CHANGELOG.md`
4. Aktualizovat dependencies: `pip install --upgrade -r requirements.txt`
5. Spustit testy
6. Restartovat server

---

**Aktualizováno:** 29. října 2024  
**Verze dokumentace:** 1.0.0
