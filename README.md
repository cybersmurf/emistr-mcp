# eMISTR MCP Server

MCP (Model Context Protocol) server pro integraci s eMISTR ERP systémem. Tento server umožňuje AI asistentům bezpečně komunikovat s databází eMISTR a poskytovat strukturované odpovědi pro Delphi aplikaci.

## 🎯 Hlavní funkce

- **Anonymizace dat**: Automatická anonymizace citlivých údajů (jména zákazníků, osobní data)
- **Strukturované odpovědi**: Unifikovaný JSON formát pro snadnou integraci s Delphi aplikací
- **Bezpečný přístup**: Read-only databázové dotazy s ochranou proti SQL injection
- **Kontextové akce**: Server vrací nejen data, ale i doporučené akce pro UI (otevření okna, filtry, atd.)

## 📋 Podporované funkce

### Zakázky (Orders)
- `get_orders` - Seznam zakázek s filtry (podpora `columns` pro filtrování polí, `active` jako integer)
- `get_order_detail` - Detail zakázky včetně operací a materiálu
- `search_orders` - Fulltextové vyhledávání v zakázkách

### Zaměstnanci (Workers)
- `get_workers` - Seznam zaměstnanců
- `get_worker_detail` - Detail zaměstnance včetně základních statistik

### Materiál (Materials)
- `get_materials` - Seznam materiálů na skladu (pole dle schématu `sklad_material`)
- `get_material_movements` - Pohyby materiálu

### Operace (Operations)
- `get_operations` - Seznam operací

### Stroje (Machines)
- `get_machines` - Seznam strojů (schéma `stroje` + `stroj_group`)

### Statistiky (Production)
- `get_production_stats` - Souhrn hodin a top operací v období (počítáno z rozdílu `finish-start`)

## 🔒 Anonymizace

Server automaticky anonymizuje:
- Jména zákazníků → `ZÁKAZNÍK_XXX`
- Jména zaměstnanců → `ZAMĚSTNANEC_YYY`
- Email adresy → `email_***@***`
- Telefonní čísla → `+420 XXX XXX XXX`
- Poznámky obsahující osobní údaje

Interní ID a čísla zakázek zůstávají zachovány pro provozní účely.

## 📦 Unifikovaný formát odpovědi

Všechny odpovědi mají jednotnou strukturu:

```json
{
  "status": "success",
  "action": {
    "type": "open_window",
    "window": "order_list",
    "filters": {
      "status": "active"
    }
  },
  "data": {
    "items": [...],
    "summary": {...},
    "metadata": {...}
  },
  "message": "Nalezeno 15 aktivních zakázek"
}
```

### Typy akcí pro Delphi aplikaci

- `open_window` - Otevřít konkrétní okno
- `apply_filter` - Aplikovat filtr
- `show_detail` - Zobrazit detail položky
- `refresh_list` - Obnovit seznam
- `show_message` - Zobrazit zprávu

## 🚀 Instalace

```bash
# Klonování repozitáře
git clone <repository-url>
cd emistr-mcp

# Vytvoření virtuálního prostředí
python -m venv venv
source venv/bin/activate  # Linux/Mac
# nebo
venv\Scripts\activate  # Windows

# Instalace závislostí
pip install -r requirements.txt

# Konfigurace
cp config.example.json config.json
# Upravte config.json s vaším DB připojením
```

## ⚙️ Konfigurace

Vytvořte `config.json`:

```json
{
  "database": {
    "host": "localhost",
    "port": 3306,
    "database": "sud_utf8_aaa",
    "user": "emistr_user",
    "password": "your_password"
  },
  "anonymization": {
    "enabled": true,
    "preserve_ids": true
  },
  "logging": {
    "level": "INFO",
    "file": "emistr_mcp.log"
  }
}
```

## 🔧 Použití s Claude Desktop

Přidejte do `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "emistr": {
      "command": "python",
      "args": ["/path/to/emistr-mcp/server.py"],
      "env": {
        "EMISTR_CONFIG": "/path/to/config.json"
      }
    }
  }
}
```

## 📝 Příklady použití

### Dotaz: "Zobraz mi aktivní zakázky"

Odpověď:
```json
{
  "status": "success",
  "action": {
    "type": "open_window",
    "window": "order_list",
    "filters": {
      "active": "ANO"
    }
  },
  "data": {
    "items": [
      {
        "id": 12345,
        "code": "2024/001",
        "name": "Výrobek A",
        "customer": "ZÁKAZNÍK_001",
        "status": "Ve výrobě",
        "start_date": "2024-01-15",
        "finish_date": "2024-02-15",
        "completion": 65.5
      }
    ],
    "summary": {
      "total_count": 15,
      "in_production": 8,
      "delayed": 2
    }
  },
  "message": "Nalezeno 15 aktivních zakázek, 2 jsou zpožděny"
}
```

### Dotaz: "Kdo pracuje na zakázce 2024/001?"

Odpověď:
```json
{
  "status": "success",
  "action": {
    "type": "show_detail",
    "window": "order_detail",
    "item_id": 12345,
    "tab": "operations"
  },
  "data": {
    "order": {
      "code": "2024/001",
      "name": "Výrobek A"
    },
    "workers": [
      {
        "worker_id": "ZAMĚSTNANEC_042",
        "operation": "Soustružení",
        "hours_worked": 15.5,
        "status": "Probíhá"
      }
    ]
  },
  "message": "Na zakázce pracuje 1 zaměstnanec"
}
```

## 🏗️ Architektura

```
emistr-mcp/
├── server.py              # Hlavní MCP server
├── database.py            # Databázové dotazy
├── anonymizer.py          # Anonymizace dat
├── response_builder.py    # Konstrukce odpovědí
├── config.py             # Konfigurace
├── requirements.txt      # Python závislosti
├── config.example.json   # Příklad konfigurace
└── README.md            # Dokumentace
```

## 🔐 Bezpečnost

- Všechny dotazy jsou READ-ONLY
- SQL injection ochrana pomocí parametrizovaných dotazů
- Automatická anonymizace osobních údajů
- Logování všech přístupů
- Žádné přímé spouštění SQL od uživatele

## 📊 Monitoring a logování

Server loguje:
- Všechny dotazy a jejich parametry
- Anonymizované výsledky
- Chyby a výjimky
- Dobu zpracování dotazů

## 🤝 Integrace s Delphi

Delphi aplikace může zpracovat odpovědi podle `action.type`:

```pascal
procedure TMainForm.ProcessMCPResponse(const JSONResponse: string);
var
  Response: TJSONObject;
  Action: TJSONObject;
  ActionType: string;
begin
  Response := TJSONObject.ParseJSONValue(JSONResponse) as TJSONObject;
  try
    Action := Response.GetValue('action') as TJSONObject;
    ActionType := Action.GetValue('type').Value;
    
    case ActionType of
      'open_window': OpenWindowFromAction(Action);
      'apply_filter': ApplyFilterFromAction(Action);
      'show_detail': ShowDetailFromAction(Action);
      'refresh_list': RefreshCurrentList;
      'show_message': ShowMessage(Response.GetValue('message').Value);
    end;
  finally
    Response.Free;
  end;
end;
```

## 📄 Licence

Interní použití pro Agerit s.r.o.

## 👥 Autoři

Vytvořeno pro eMISTR 2024 systém
