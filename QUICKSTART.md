# eMISTR MCP - Quick Start

Rychlý start pro zprovoznění MCP serveru pro eMISTR během 5 minut.

## ⚡ Rychlá instalace

```bash
# 1. Stažení a rozbalení
cd ~/Projects
unzip emistr-mcp.zip
cd emistr-mcp

# 2. Vytvoření virtuálního prostředí
python -m venv venv
source venv/bin/activate  # Linux/Mac
# nebo
venv\Scripts\activate  # Windows

# 3. Instalace závislostí
pip install -r requirements.txt

# 4. Konfigurace
cp config.example.json config.json
nano config.json  # Upravte DB credentials
```

## ⚙️ Minimální konfigurace

Upravte pouze tyto řádky v `config.json`:

```json
{
  "database": {
    "host": "your-db-host",
    "user": "your-username",
    "password": "your-password",
    "database": "sud_utf8_aaa"
  }
}
```

## ✅ Test

```bash
python test_server.py
```

Měli byste vidět:
```
✅ Připojení úspěšné
✅ Načteno 5 zakázek
✅ Data anonymizována
```

## 🔗 Připojení ke Claude Desktop

### Najděte config soubor:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

### Přidejte tento kód:

```json
{
  "mcpServers": {
    "emistr": {
      "command": "python",
      "args": ["/absolutni/cesta/k/emistr-mcp/server.py"],
      "env": {
        "EMISTR_CONFIG": "/absolutni/cesta/k/config.json"
      }
    }
  }
}
```

## 🎯 První test

1. Restartujte Claude Desktop
2. V novém chatu napište:

```
Zobraz mi aktivní zakázky v eMISTR
```

3. Měli byste dostat strukturovanou JSON odpověď

## 📖 Co dál?

- Kompletní dokumentace: `README.md`
- Instalační průvodce: `INSTALL.md`
- Příklady použití: `EXAMPLES.md`
- Delphi integrace: `DELPHI_INTEGRATION.md`

## 🆘 Rychlé řešení problémů

### "Can't connect to database"
→ Zkontrolujte `config.json` credentials

### "ModuleNotFoundError: mcp"
→ Aktivujte virtuální prostředí: `source venv/bin/activate`

### Claude nevidí MCP server
→ Použijte absolutní cesty v claude_desktop_config.json

### Server se nespustí
→ Spusťte manuálně: `python server.py` a podívejte se na chyby

## 💪 Základní dotazy

Po úspěšném nastavení zkuste:

```
Zobraz aktivní zakázky
Kdo pracuje na zakázce 2024/001?
Kolik máme materiálu na skladu?
Které stroje jsou volné?
Jaká byla produktivita tento měsíc?
```

## 📞 Potřebujete pomoc?

Detailní průvodce: `INSTALL.md`
IT podpora: it@agerit.cz
