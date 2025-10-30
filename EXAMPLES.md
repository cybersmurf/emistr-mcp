# Příklady použití eMISTR MCP

Tento dokument obsahuje praktické příklady dotazů a odpovědí pro různé scénáře.

## 📋 Základní dotazy na zakázky

### Zobrazení aktivních zakázek

**Dotaz:**
```
Zobraz mi všechny aktivní zakázky
```

**Odpověď MCP:**
```json
{
  "status": "success",
  "action": {
    "type": "open_window",
    "window": "order_list",
    "filters": {
      "status": "ANO"
    }
  },
  "data": {
    "items": [
      {
        "id": "12345",
        "code": "2024/001",
        "name": "Hřídel průměr 50mm",
        "customer_name": "ZÁKAZNÍK_A1B2C3",
        "start": "2024-01-15",
        "finish": "2024-02-15",
        "kusu": "100.000",
        "prevedeno": "75.000",
        "priorita": 5
      }
    ],
    "summary": {
      "total_count": 15,
      "delayed_count": 2
    }
  },
  "message": "Nalezeno 15 aktivních zakázek, 2 jsou zpožděny"
}
```

### Zpožděné zakázky

**Dotaz:**
```
Které zakázky jsou zpožděné?
```

**Odpověď:**
Server filtruje zakázky s `finish < CURDATE()` a `active = 'ANO'`

### Vyhledání konkrétní zakázky

**Dotaz:**
```
Najdi zakázku s kódem 2024/001
```

**Odpověď:**
```json
{
  "status": "success",
  "action": {
    "type": "show_detail",
    "window": "order_detail",
    "item_id": 12345
  },
  "data": {
    "order": {
      "code": "2024/001",
      "name": "Hřídel průměr 50mm",
      "customer_name": "ZÁKAZNÍK_A1B2C3",
      "kusu": "100.000",
      "prevedeno": "75.000",
      "user_time": "480",
      "real_time": "360"
    },
    "operations": [
      {
        "operation_name": "Soustružení",
        "user_time": "120",
        "real_time": "95",
        "vyrobenocelkem": "75.000"
      }
    ],
    "summary": {
      "completion_percent": 75.0,
      "operations_count": 5,
      "operations_completed": 3
    }
  }
}
```

## 👥 Dotazy na zaměstnance

### Seznam aktivních zaměstnanců

**Dotaz:**
```
Kdo dnes pracuje?
```

nebo

```
Zobraz aktivní zaměstnance
```

**Odpověď:**
```json
{
  "status": "success",
  "action": {
    "type": "open_window",
    "window": "worker_list",
    "filters": {
      "status": "ANO"
    }
  },
  "data": {
    "items": [
      {
        "id": "42",
        "bar_id": "0001",
        "name": "ZAMĚSTNANEC_A1B2C3",
        "group_name": "Výroba",
        "profese": "Soustružník",
        "active": "ANO"
      }
    ],
    "summary": {
      "total_count": 25,
      "active_count": 25
    }
  }
}
```

### Výkon zaměstnance

**Dotaz:**
```
Kolik hodin odpracoval zaměstnanec 0001 za poslední měsíc?
```

**Odpověď:**
```json
{
  "status": "success",
  "action": {
    "type": "show_detail",
    "window": "worker_detail",
    "item_id": 42
  },
  "data": {
    "worker": {
      "bar_id": "0001",
      "name": "ZAMĚSTNANEC_A1B2C3",
      "group_name": "Výroba"
    },
    "stats": {
      "orders_count": 15,
      "total_hours": 168,
      "avg_hours_per_order": 11.2,
      "last_work_date": "2024-10-29"
    },
    "summary": {
      "orders_last_30_days": 15,
      "total_hours_last_30_days": 168,
      "avg_hours_per_order": 11.2
    }
  }
}
```

## 📦 Dotazy na materiál

### Stav skladu

**Dotaz:**
```
Kolik máme materiálu na skladu?
```

**Odpověď:**
```json
{
  "status": "success",
  "action": {
    "type": "open_window",
    "window": "material_list"
  },
  "data": {
    "items": [
      {
        "bar_id": "MAT001",
        "name": "Ocel 11500",
        "stock_quantity": "1250.500",
        "min_quantity": "500.000",
        "jednotka": "kg",
        "warehouse_name": "Hlavní sklad"
      }
    ],
    "summary": {
      "total_count": 125,
      "low_stock_count": 0,
      "total_value": 2150000.00
    }
  }
}
```

### Materiály s nízkou zásobou

**Dotaz:**
```
Které materiály mají nízkou zásobu?
```

**Odpověď:**
Server filtruje materiály kde `mnozstvi < min_mnozstvi` a zvýrazní je.

### Pohyby materiálu

**Dotaz:**
```
Zobraz pohyby materiálu za poslední týden
```

**Odpověď:**
```json
{
  "data": {
    "items": [
      {
        "material_name": "Ocel 11500",
        "mnozstvi": "50.000",
        "datum": "2024-10-25",
        "typ_pohybu": "V",
        "order_id": "12345"
      }
    ],
    "summary": {
      "movements_count": 45,
      "total_in": 500,
      "total_out": 320
    }
  }
}
```

## 🔧 Dotazy na operace a stroje

### Dostupné operace

**Dotaz:**
```
Jaké operace máme definované?
```

**Odpověď:**
```json
{
  "data": {
    "items": [
      {
        "name": "Soustružení",
        "bar_id": "OP001",
        "user_price": "450.00",
        "user_time": "60",
        "group_name": "Obrábění"
      }
    ]
  }
}
```

### Stav strojů

**Dotaz:**
```
Které stroje jsou momentálně volné?
```

**Odpověď:**
```json
{
  "action": {
    "type": "open_window",
    "window": "machine_list",
    "filters": {
      "status_filter": "idle"
    }
  },
  "data": {
    "items": [
      {
        "name": "Soustruh SU250",
        "bar_id": "STR001",
        "current_status": "idle",
        "active": "ANO"
      }
    ],
    "summary": {
      "total_count": 15,
      "busy_count": 8,
      "idle_count": 7
    }
  },
  "message": "Nalezeno 15 strojů (8 v provozu, 7 nečinných)"
}
```

## 📊 Statistiky a analýzy

### Produktivita za období

**Dotaz:**
```
Jaká byla produktivita za říjen 2024?
```

**Odpověď:**
```json
{
  "action": {
    "type": "open_window",
    "window": "production_stats",
    "period": {
      "from": "2024-10-01",
      "to": "2024-10-31"
    }
  },
  "data": {
    "daily_stats": [
      {
        "date": "2024-10-01",
        "total_hours": 168,
        "workers_count": 25,
        "orders_count": 15
      }
    ],
    "top_operations": [
      {
        "name": "Soustružení",
        "count": 145,
        "total_hours": 1250
      }
    ],
    "summary": {
      "total_hours": 3360,
      "average_workers_per_day": 24.5,
      "days_count": 20,
      "average_hours_per_day": 168
    }
  }
}
```

## 🔍 Složitější dotazy

### Kombinované dotazy

**Dotaz:**
```
Zobraz zakázky pro zákazníka XYZ, které jsou aktivní a mají prioritu vyšší než 5
```

MCP server automaticky vytvoří příslušné filtry.

### Kontextové dotazy

**Dotaz 1:**
```
Zobraz zakázku 2024/001
```

**Dotaz 2 (navazuje):**
```
Kdo na ní pracuje?
```

Server si pamatuje kontext a vrátí zaměstnance pracující na zakázce 2024/001.

### Cross-reference dotazy

**Dotaz:**
```
Kolik materiálu jsme spotřebovali na zakázce 2024/001?
```

**Odpověď:**
Server spojí data z tabulek `material` a `c_order`.

## 🎯 Praktické use cases

### Ranní meeting

**Dotaz:**
```
Připrav mi přehled pro ranní poradu
```

**Očekávaná odpověď:**
- Počet aktivních zakázek
- Zpožděné zakázky
- Volné stroje
- Materiály s nízkou zásobou

### Plánování výroby

**Dotaz:**
```
Které zakázky mají termín dodání do 7 dnů?
```

**Odpověď:**
Server filtruje zakázky s `finish` mezi dnes a dnes + 7 dnů.

### Kontrola kvality

**Dotaz:**
```
Zobraz zakázky s vysokou prioritou, které ještě nejsou dokončené
```

### Sledování nákladů

**Dotaz:**
```
Jaké jsou celkové náklady na materiál u zakázky 2024/001?
```

**Odpověď:**
```json
{
  "data": {
    "materials": [
      {
        "material_name": "Ocel 11500",
        "mnozstvi": "50.000",
        "cena_nakup": "120.00",
        "cena_celkem": "6000.00"
      }
    ],
    "summary": {
      "total_material_cost": 12500.00
    }
  }
}
```

## 💡 Tipy pro efektivní použití

### 1. Používejte přirozený jazyk

✅ **Dobré:**
- "Zobraz aktivní zakázky"
- "Kdo pracuje na zakázce 2024/001?"
- "Kolik máme materiálu na skladu?"

❌ **Není nutné:**
- "SELECT * FROM c_order WHERE active='ANO'"
- "get_orders(status='ANO')"

### 2. Buďte konkrétní

✅ **Dobré:**
- "Zobraz zakázky s termínem do konce října"
- "Které zakázky jsou zpožděny více než týden?"

❌ **Příliš vágní:**
- "Zobraz nějaké zakázky"
- "Co se děje ve výrobě?"

### 3. Využívejte kontextu

První dotaz:
```
Zobraz detail zakázky 2024/001
```

Následující dotazy mohou být kratší:
```
Kdo na ní pracuje?
Kolik materiálu spotřebovala?
Kdy bude hotová?
```

### 4. Kombinujte filtry

```
Zobraz aktivní zakázky pro zákazníka ABC s prioritou vyšší než 5, které mají termín do konce měsíce
```

## 🔐 Bezpečnostní poznámky

### Co server anonymizuje:

✅ **Anonymizováno:**
- Jména zákazníků → `ZÁKAZNÍK_XXXXX`
- Jména zaměstnanců → `ZAMĚSTNANEC_XXXXX`
- Email adresy → `email_***@***`
- Telefonní čísla → `+420 XXX XXX XXX`
- IČO/DIČ → `********`

✅ **Zachováno:**
- ID zakázek a operací
- Kódy zakázek (2024/001)
- Technická data (množství, časy, ceny)
- Interní identifikátory (bar_id)

### Příklad anonymizovaných dat:

**Originál (v databázi):**
```
Zákazník: "ABC Manufacturing s.r.o."
Email: "jan.novak@abc.cz"
Telefon: "+420 123 456 789"
```

**Anonymizováno (v odpovědi):**
```
Zákazník: "ZÁKAZNÍK_A1B2C3"
Email: "email_***@***"
Telefon: "+420 XXX XXX XXX"
```

## 🚀 Pokročilé použití

### Export dat do Delphi

Data z MCP lze přímo použít v Delphi aplikaci:

```pascal
// Zpracování odpovědi v Delphi
procedure ProcessMCPResponse(const JSONStr: string);
var
  Response: TMCPResponse;
begin
  Response := TMCPResponseParser.Parse(JSONStr);
  
  case Response.Action.ActionType of
    atOpenWindow: 
      OpenWindow(Response.Action.Window, Response.Data);
    atShowDetail:
      ShowDetail(Response.Action.ItemID);
  end;
end;
```

### Automatické reporty

MCP server může poskytovat data pro automatické reporty:
- Denní přehled výroby
- Týdenní statistiky
- Měsíční výkazy

### Integrace s dalšími systémy

Data z MCP lze exportovat do:
- Excel reportů
- PDF dokumentů
- Dashboardů
- Business Intelligence nástrojů
