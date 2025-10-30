# Integrace eMISTR MCP s Delphi aplikací

## Přehled

Tento dokument popisuje, jak Delphi aplikace eMISTR může komunikovat s MCP serverem a zpracovávat jeho odpovědi.

## Formát odpovědi

Všechny odpovědi z MCP serveru mají jednotnou JSON strukturu:

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
  "message": "Nalezeno 15 aktivních zakázek"
}
```

## Typy akcí (action.type)

### 1. `open_window` - Otevření okna

Otevře konkrétní okno v aplikaci s možnými filtry.

**Parametry:**
- `window` - název okna k otevření
- `filters` - objekty filtrů k aplikování
- `item_id` - volitelné ID položky

**Příklad:**
```json
{
  "type": "open_window",
  "window": "order_list",
  "filters": {
    "active": 1,
    "date_from": "2024-01-01"
  }
}
```

**Podporovaná okna:**
- `order_list` - Seznam zakázek
- `order_detail` - Detail zakázky
- `worker_list` - Seznam zaměstnanců
- `worker_detail` - Detail zaměstnance
- `material_list` - Seznam materiálů
- `material_movements` - Pohyby materiálu
- `operation_list` - Seznam operací
- `machine_list` - Seznam strojů
- `production_stats` - Statistiky výroby
- `search_results` - Výsledky vyhledávání

### 2. `show_detail` - Zobrazení detailu

Otevře detail konkrétní položky.

**Parametry:**
- `window` - název okna detailu
- `item_id` - ID položky k zobrazení
- `tab` - volitelně konkrétní záložka

**Příklad:**
```json
{
  "type": "show_detail",
  "window": "order_detail",
  "item_id": 12345,
  "tab": "operations"
}
```

### 3. `apply_filter` - Aplikování filtru

Aplikuje filtr na aktuální zobrazení.

**Parametry:**
- `filters` - objekt s filtry

**Příklad:**
```json
{
  "type": "apply_filter",
  "filters": {
    "status": "ANO",
    "customer_id": 100
  }
}
```

### 4. `refresh_list` - Obnovení seznamu

Obnoví aktuální seznam bez změny filtrů.

**Příklad:**
```json
{
  "type": "refresh_list"
}
```

### 5. `show_message` - Zobrazení zprávy

Zobrazí uživateli informační zprávu.

**Parametry:**
- `message` - text zprávy
- `message_type` - typ zprávy (info, warning, error)

**Příklad:**
```json
{
  "type": "show_message",
  "message": "Zakázka byla úspěšně uložena",
  "message_type": "info"
}
```

## Implementace v Delphi

### Základní parser

```pascal
unit MCPResponseParser;

interface

uses
  System.SysUtils, System.JSON, System.Classes;

type
  TMCPActionType = (atOpenWindow, atShowDetail, atApplyFilter, atRefreshList, atShowMessage, atUnknown);
  
  TMCPAction = record
    ActionType: TMCPActionType;
    Window: string;
    ItemID: Integer;
    Tab: string;
    Filters: TJSONObject;
    Message: string;
    MessageType: string;
  end;
  
  TMCPResponse = record
    Status: string;
    Timestamp: TDateTime;
    Action: TMCPAction;
    Data: TJSONObject;
    Message: string;
  end;

  TMCPResponseParser = class
  private
    class function ParseActionType(const AType: string): TMCPActionType;
  public
    class function Parse(const JSONString: string): TMCPResponse;
    class procedure ProcessAction(const Action: TMCPAction);
  end;

implementation

class function TMCPResponseParser.ParseActionType(const AType: string): TMCPActionType;
begin
  if AType = 'open_window' then
    Result := atOpenWindow
  else if AType = 'show_detail' then
    Result := atShowDetail
  else if AType = 'apply_filter' then
    Result := atApplyFilter
  else if AType = 'refresh_list' then
    Result := atRefreshList
  else if AType = 'show_message' then
    Result := atShowMessage
  else
    Result := atUnknown;
end;

class function TMCPResponseParser.Parse(const JSONString: string): TMCPResponse;
var
  JSONObj, ActionObj: TJSONObject;
begin
  JSONObj := TJSONObject.ParseJSONValue(JSONString) as TJSONObject;
  try
    Result.Status := JSONObj.GetValue<string>('status');
    Result.Message := JSONObj.GetValue<string>('message');
    
    // Parse action
    ActionObj := JSONObj.GetValue<TJSONObject>('action');
    if Assigned(ActionObj) then
    begin
      Result.Action.ActionType := ParseActionType(ActionObj.GetValue<string>('type'));
      
      // Parse podle typu akce
      case Result.Action.ActionType of
        atOpenWindow:
        begin
          Result.Action.Window := ActionObj.GetValue<string>('window');
          if ActionObj.TryGetValue<TJSONObject>('filters', Result.Action.Filters) then
            Result.Action.Filters := Result.Action.Filters.Clone as TJSONObject;
        end;
        
        atShowDetail:
        begin
          Result.Action.Window := ActionObj.GetValue<string>('window');
          Result.Action.ItemID := ActionObj.GetValue<Integer>('item_id');
          ActionObj.TryGetValue<string>('tab', Result.Action.Tab);
        end;
        
        atShowMessage:
        begin
          Result.Action.Message := ActionObj.GetValue<string>('message');
          ActionObj.TryGetValue<string>('message_type', Result.Action.MessageType);
        end;
      end;
    end;
    
    // Parse data
    Result.Data := JSONObj.GetValue<TJSONObject>('data').Clone as TJSONObject;
    
  finally
    JSONObj.Free;
  end;
end;

class procedure TMCPResponseParser.ProcessAction(const Action: TMCPAction);
begin
  case Action.ActionType of
    atOpenWindow:
      OpenWindowWithFilters(Action.Window, Action.Filters);
    
    atShowDetail:
      OpenDetailWindow(Action.Window, Action.ItemID, Action.Tab);
    
    atApplyFilter:
      ApplyFiltersToCurrentView(Action.Filters);
    
    atRefreshList:
      RefreshCurrentList;
    
    atShowMessage:
      ShowUserMessage(Action.Message, Action.MessageType);
  end;
end;

end.
```

### Ukázka použití

```pascal
procedure TMainForm.ProcessMCPResponse(const JSONResponse: string);
var
  Response: TMCPResponse;
  Items: TJSONArray;
  i: Integer;
begin
  Response := TMCPResponseParser.Parse(JSONResponse);
  
  // Zpracování podle statusu
  if Response.Status <> 'success' then
  begin
    ShowMessage('Chyba: ' + Response.Message);
    Exit;
  end;
  
  // Zpracování akce
  TMCPResponseParser.ProcessAction(Response.Action);
  
  // Zpracování dat
  if Response.Data.TryGetValue<TJSONArray>('items', Items) then
  begin
    // Naplnění gridu nebo seznamu
    for i := 0 to Items.Count - 1 do
    begin
      AddItemToGrid(Items.Items[i] as TJSONObject);
    end;
  end;
  
  // Zobrazení summary
  UpdateSummary(Response.Data.GetValue<TJSONObject>('summary'));
  
  // Zobrazení zprávy
  StatusBar1.SimpleText := Response.Message;
end;
```

### Otevírání oken

```pascal
procedure OpenWindowWithFilters(const WindowName: string; Filters: TJSONObject);
var
  Form: TForm;
begin
  // Podle jména okna
  if WindowName = 'order_list' then
  begin
    Form := TOrderListForm.Create(Application);
    TOrderListForm(Form).ApplyFilters(Filters);
  end
  else if WindowName = 'order_detail' then
  begin
    Form := TOrderDetailForm.Create(Application);
  end
  else if WindowName = 'worker_list' then
  begin
    Form := TWorkerListForm.Create(Application);
    TWorkerListForm(Form).ApplyFilters(Filters);
  end
  // ... další okna
  
  if Assigned(Form) then
    Form.Show;
end;
```

### Aplikování filtrů

```pascal
procedure TOrderListForm.ApplyFilters(Filters: TJSONObject);
var
  Status, DateFrom, DateTo: string;
  CustomerID: Integer;
begin
  // Parse filtrů
  if Filters.TryGetValue<string>('status', Status) then
    ComboBoxStatus.Text := Status;
  
  if Filters.TryGetValue<Integer>('customer_id', CustomerID) then
    EditCustomerID.Text := IntToStr(CustomerID);
  
  if Filters.TryGetValue<string>('date_from', DateFrom) then
    DateEditFrom.Date := ISO8601ToDate(DateFrom);
  
  if Filters.TryGetValue<string>('date_to', DateTo) then
    DateEditTo.Date := ISO8601ToDate(DateTo);
  
  // Aplikování filtru
  RefreshData;
end;
```

### Naplnění gridu daty

```pascal
procedure TOrderListForm.LoadOrdersFromJSON(Items: TJSONArray);
var
  i: Integer;
  Item: TJSONObject;
  Row: Integer;
begin
  StringGrid1.RowCount := Items.Count + 1; // +1 pro header
  
  for i := 0 to Items.Count - 1 do
  begin
    Item := Items.Items[i] as TJSONObject;
    Row := i + 1;
    
    StringGrid1.Cells[0, Row] := Item.GetValue<string>('code');
    StringGrid1.Cells[1, Row] := Item.GetValue<string>('name');
    StringGrid1.Cells[2, Row] := Item.GetValue<string>('customer_name');
    StringGrid1.Cells[3, Row] := Item.GetValue<string>('start');
    StringGrid1.Cells[4, Row] := Item.GetValue<string>('finish');
    StringGrid1.Cells[5, Row] := Item.GetValue<string>('active');
    
    // Zvýraznění zpožděných zakázek
    if IsOrderDelayed(Item) then
      StringGrid1.RowColors[Row] := clRed;
  end;
end;
```

## Příklady odpovědí

### Seznam zakázek

```json
{
  "status": "success",
  "timestamp": "2024-10-29T10:30:00",
  "action": {
    "type": "open_window",
    "window": "order_list",
    "filters": {
      "active": 1
    }
  },
  "data": {
    "items": [
      {
        "id": 12345,
        "code": "2024/001",
        "name": "Výrobek A",
        "customer_name": "ZÁKAZNÍK_001",
        "start": "2024-01-15",
        "finish": "2024-02-15",
        "active": 1
      }
    ],
    "summary": {
      "total_count": 15
    },
    "metadata": {
      "columns": [
        {"key": "code", "label": "Kód zakázky", "type": "string"},
        {"key": "name", "label": "Název", "type": "string"}
      ]
    }
  },
  "message": "Nalezeno 15 aktivních zakázek, 2 jsou zpožděny"
}
```

### Detail zakázky

```json
{
  "status": "success",
  "action": {
    "type": "show_detail",
    "window": "order_detail",
    "item_id": 12345,
    "tabs": ["header", "operations", "materials"]
  },
  "data": {
    "order": {
      "id": "12345",
      "code": "2024/001",
      "name": "Výrobek A",
      "customer_name": "ZÁKAZNÍK_001"
    },
    "operations": [
      {
        "operation_name": "Soustružení",
        "user_time": "120",
        "real_time": "95",
        "vyrobenocelkem": "65.500"
      }
    ],
    "summary": {
      "completion_percent": 65.5,
      "operations_count": 5,
      "operations_completed": 3
    }
  },
  "message": "Detail zakázky 2024/001 - Výrobek A"
}
```

## Tipy pro implementaci

1. **Cachování parsovaných JSON objektů** - nemusíte parsovat znovu při každém přístupu
2. **Async načítání** - použijte TTask pro asynchronní zpracování odpovědí
3. **Error handling** - vždy kontrolujte status a zpracujte chyby
4. **Validace dat** - kontrolujte, zda JSON obsahuje očekávaná pole
5. **Memory management** - nezapomeňte uvolnit JSON objekty pomocí Free

## Bezpečnost

- Data jsou automaticky anonymizována na straně MCP serveru
- Citlivé údaje (jména, kontakty) jsou nahrazeny placeholdery
- Interní ID a kódy zakázek jsou zachovány pro provozní účely
- Log všech dotazů je uložen na serveru
