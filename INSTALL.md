# Instalační průvodce eMISTR MCP Server

Tento dokument vás provede instalací a konfigurací MCP serveru pro eMISTR.

## Předpoklady

- Python 3.11 nebo vyšší
- Přístup k MariaDB databázi eMISTR
- Claude Desktop (pro testování)

## Krok 1: Příprava prostředí

### Windows

```powershell
# Otevřete PowerShell jako administrátor

# Ověření Python
python --version

# Pokud Python není nainstalován, stáhněte z python.org
```

### Linux/Mac

```bash
# Otevřete terminál

# Ověření Python
python3 --version

# Instalace Python (pokud chybí)
# Ubuntu/Debian:
sudo apt-get install python3 python3-pip python3-venv

# Mac:
brew install python3
```

## Krok 2: Stažení a instalace

```bash
# Vytvoření adresáře pro projekt
mkdir emistr-mcp
cd emistr-mcp

# Stažení souborů (nebo rozbalení archivu)
# Pokud máte soubory jako ZIP:
# unzip emistr-mcp.zip

# Vytvoření virtuálního prostředí
python -m venv venv

# Aktivace virtuálního prostředí
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalace závislostí
pip install -r requirements.txt
```

## Krok 3: Konfigurace databáze

```bash
# Zkopírování ukázkové konfigurace
cp config.example.json config.json

# Editace konfigurace (použijte váš oblíbený editor)
# Windows:
notepad config.json
# Linux/Mac:
nano config.json
```

Upravte následující hodnoty v `config.json`:

```json
{
  "database": {
    "host": "your-database-host",
    "port": 3306,
    "database": "sud_utf8_aaa",
    "user": "your-username",
    "password": "your-password"
  }
}
```

## Krok 4: Test připojení

```bash
# Spuštění testů
python test_server.py
```

Měli byste vidět výstup:

```
============================================================
eMISTR MCP Server - Testovací sada
============================================================
🔌 Test připojení k databázi...
✅ Připojení úspěšné
✅ Verze MariaDB: 10.x.x

📋 Test načtení zakázek...
✅ Načteno 5 zakázek
...
```

Pokud nějaký test selže, zkontrolujte:
- Databázové přihlašovací údaje
- Síťové připojení k databázi
- Oprávnění databázového uživatele

## Krok 5: Konfigurace Claude Desktop

### Nalezení konfiguračního souboru

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Mac:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

### Přidání MCP serveru

Otevřete `claude_desktop_config.json` a přidejte:

```json
{
  "mcpServers": {
    "emistr": {
      "command": "python",
      "args": [
        "C:\\cesta\\k\\emistr-mcp\\server.py"
      ],
      "env": {
        "EMISTR_CONFIG": "C:\\cesta\\k\\emistr-mcp\\config.json"
      }
    }
  }
}
```

**Poznámka:** 
- Windows: Použijte zpětná lomítka `\\` nebo lomítka `/`
- Linux/Mac: Použijte absolutní cestu začínající `/`

### Příklad pro různé platformy

**Windows:**
```json
{
  "mcpServers": {
    "emistr": {
      "command": "C:\\Users\\uzivatel\\emistr-mcp\\venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\uzivatel\\emistr-mcp\\server.py"
      ],
      "env": {
        "EMISTR_CONFIG": "C:\\Users\\uzivatel\\emistr-mcp\\config.json"
      }
    }
  }
}
```

**Linux/Mac:**
```json
{
  "mcpServers": {
    "emistr": {
      "command": "/home/uzivatel/emistr-mcp/venv/bin/python",
      "args": [
        "/home/uzivatel/emistr-mcp/server.py"
      ],
      "env": {
        "EMISTR_CONFIG": "/home/uzivatel/emistr-mcp/config.json"
      }
    }
  }
}
```

## Krok 6: Restart Claude Desktop

1. Ukončete Claude Desktop úplně
2. Spusťte Claude Desktop znovu
3. V novém chatu zkuste: "Zobraz aktivní zakázky v eMISTR"

## Krok 7: Ověření funkčnosti

V Claude Desktop zkuste následující dotazy:

```
Zobraz mi aktivní zakázky v eMISTR
```

```
Jaký je stav zakázky 2024/001?
```

```
Kdo pracuje na zakázkách?
```

Měli byste obdržet strukturované odpovědi ve formátu JSON.

## Řešení problémů

### Python není rozpoznán

**Windows:**
1. Otevřete "System Properties" → "Environment Variables"
2. Přidejte Python do PATH
3. Restartujte PowerShell

**Linux/Mac:**
```bash
# Přidejte do ~/.bashrc nebo ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"
```

### Chyba připojení k databázi

```
❌ Chyba připojení: Can't connect to MySQL server
```

**Řešení:**
1. Ověřte, že MariaDB běží: `mysql -u username -p`
2. Zkontrolujte firewall
3. Ověřte přihlašovací údaje v config.json
4. Zkontrolujte síťové připojení

### ModuleNotFoundError

```
ModuleNotFoundError: No module named 'mcp'
```

**Řešení:**
```bash
# Aktivujte virtuální prostředí
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Přeinstalujte závislosti
pip install -r requirements.txt
```

### Claude Desktop nevidí MCP server

**Řešení:**
1. Zkontrolujte cesty v claude_desktop_config.json
2. Použijte absolutní cesty (ne relativní)
3. Restartujte Claude Desktop
4. Zkontrolujte logy:
   - Windows: `%APPDATA%\Claude\logs\`
   - Mac: `~/Library/Logs/Claude/`
   - Linux: `~/.config/Claude/logs/`

### Server se nespustí

**Zkontrolujte logs:**
```bash
# Spusťte server manuálně pro zobrazení chyb
python server.py
```

Běžné problémy:
- Chybějící config.json
- Špatná syntaxe JSON v config.json
- Chybějící Python moduly

## Aktualizace

Pro aktualizaci serveru:

```bash
# Aktivujte virtuální prostředí
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Aktualizujte závislosti
pip install --upgrade -r requirements.txt

# Restartujte Claude Desktop
```

## Odinstalace

```bash
# Deaktivujte virtuální prostředí
deactivate

# Smažte adresář
rm -rf emistr-mcp  # Linux/Mac
rmdir /s emistr-mcp  # Windows

# Odeberte konfiguraci z Claude Desktop
# Otevřete claude_desktop_config.json a odeberte sekci "emistr"
```

## Podpora

Pro problémy nebo dotazy kontaktujte:
- IT oddělení Agerit s.r.o.
- Email: it@agerit.cz

## Bezpečnostní poznámky

1. **Hesla**: Nikdy nesdílejte config.json s hesly
2. **Přístup**: Server má pouze READ-ONLY přístup k databázi
3. **Anonymizace**: Osobní údaje jsou automaticky anonymizovány
4. **Logování**: Všechny dotazy jsou logovány pro audit

## Pokročilá konfigurace

### Vlastní port databáze

V config.json změňte:
```json
"database": {
  "port": 3307
}
```

### Vypnutí anonymizace (pouze pro vývoj)

```json
"anonymization": {
  "enabled": false
}
```

⚠️ **Varování:** Vypínejte pouze v izolovaném vývojovém prostředí!

### Úprava limitů

```json
"limits": {
  "max_query_results": 2000,
  "default_page_size": 100
}
```

### Vlastní cesta k logu

```json
"logging": {
  "file": "/var/log/emistr_mcp/server.log"
}
```

## Automatické spuštění (pokročilé)

### Windows - Task Scheduler

1. Otevřete Task Scheduler
2. Create Basic Task
3. Trigger: At startup
4. Action: Start a program
5. Program: `C:\cesta\k\venv\Scripts\python.exe`
6. Arguments: `C:\cesta\k\server.py`

### Linux - systemd

Vytvořte `/etc/systemd/system/emistr-mcp.service`:

```ini
[Unit]
Description=eMISTR MCP Server
After=network.target

[Service]
Type=simple
User=emistr
WorkingDirectory=/home/emistr/emistr-mcp
Environment="EMISTR_CONFIG=/home/emistr/emistr-mcp/config.json"
ExecStart=/home/emistr/emistr-mcp/venv/bin/python server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Povolení a spuštění:
```bash
sudo systemctl enable emistr-mcp
sudo systemctl start emistr-mcp
sudo systemctl status emistr-mcp
```
