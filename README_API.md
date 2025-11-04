# eMISTR REST/OpenAPI Adapter

REST/OpenAPI adaptér pro eMISTR MCP Server umožňující přístup k MCP nástrojům přes standardní REST API s automaticky generovanou OpenAPI dokumentací.

## 🚀 Spuštění v Dockeru

### Rychlý start

```bash
# Build a spuštění obou služeb (MCP server + REST API)
docker compose up --build -d

# Kontrola běžících kontejnerů
docker compose ps

# Logy REST API
docker compose logs -f emistr-api

# Logy MCP serveru
docker compose logs -f emistr-mcp
```

### Dostupné služby

Po spuštění máte k dispozici:

- **REST API**: http://localhost:8000
  - Swagger UI: http://localhost:8000/docs
  - ReDoc: http://localhost:8000/redoc
  - OpenAPI JSON: http://localhost:8000/openapi.json
  - Health check: http://localhost:8000/health

- **MCP Server** (JSON-RPC): http://localhost:9201/mcp

## 📡 REST API Endpointy

### Základní

- `GET /health` - Health check
- `GET /tools` - Seznam dostupných MCP nástrojů

### Zakázky (Orders)

- `GET /orders` - Seznam zakázek
  - Query parametry: `status`, `customer_id`, `date_from`, `date_to`, `limit`, `offset`, `columns`
- `GET /orders/{order_id}` - Detail zakázky
- `GET /orders:search` - Fulltextové vyhledávání
  - Query parametry: `search_term`, `limit`

### Zaměstnanci (Workers)

- `GET /workers` - Seznam zaměstnanců
  - Query parametry: `status`, `group_name`, `limit`
- `GET /workers/{worker_id}` - Detail zaměstnance

### Materiál (Materials)

- `GET /materials` - Seznam materiálů
  - Query parametry: `low_stock_only`, `limit`
- `GET /materials/movements` - Pohyby materiálu
  - Query parametry: `material_id`, `date_from`, `date_to`, `limit`

### Operace (Operations)

- `GET /operations` - Seznam operací
  - Query parametry: `operation_group`, `limit`

### Stroje (Machines)

- `GET /machines` - Seznam strojů
  - Query parametry: `status_filter`, `limit`

### Statistiky (Production)

- `GET /production/stats` - Statistiky výroby
  - Query parametry: `date_from` (povinný), `date_to` (povinný)

## 📝 Příklady použití

### cURL

```bash
# Health check
curl http://localhost:8000/health

# Seznam strojů
curl "http://localhost:8000/machines?limit=5"

# Seznam zakázek s filtrem
curl "http://localhost:8000/orders?status=ANO&limit=10"

# Detail zakázky
curl http://localhost:8000/orders/12345

# Vyhledávání zakázek
curl "http://localhost:8000/orders:search?search_term=ABC&limit=20"

# Statistiky výroby
curl "http://localhost:8000/production/stats?date_from=2024-01-01&date_to=2024-01-31"
```

### JavaScript/Fetch

```javascript
// Seznam strojů
const machines = await fetch('http://localhost:8000/machines?limit=5')
  .then(res => res.json());

// Detail zakázky
const order = await fetch('http://localhost:8000/orders/12345')
  .then(res => res.json());

// Vyhledávání
const results = await fetch('http://localhost:8000/orders:search?search_term=ABC')
  .then(res => res.json());
```

### Python/Requests

```python
import requests

# Seznam zakázek
response = requests.get('http://localhost:8000/orders', params={
    'status': 'ANO',
    'limit': 10
})
orders = response.json()

# Detail zaměstnance
worker = requests.get('http://localhost:8000/workers/42').json()
```

## 🔧 Formát odpovědi

Všechny endpointy vrací unifikovaný formát z `ResponseBuilder`:

```json
{
  "status": "success",
  "timestamp": "2024-01-15T10:30:00",
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

## 🛠️ Lokální vývoj (bez Dockeru)

```bash
# Instalace závislostí
pip install -r requirements.txt

# Spuštění REST API
python -m uvicorn api_adapter:app --reload --port 8000

# Nebo přímo
python api_adapter.py
```

## 🔒 Bezpečnost

- **CORS**: Aktuálně povoleny všechny originy (`*`). Pro produkci upravte v `api_adapter.py`:
  ```python
  allow_origins=["https://your-webui-domain.com"]
  ```

- **Autentizace**: Pro přidání API klíče/Bearer tokenu upravte `api_adapter.py` a přidejte FastAPI dependency.

## 🐛 Troubleshooting

### Kontejner se nespustí

```bash
# Kontrola logů
docker compose logs emistr-api

# Rebuild bez cache
docker compose build --no-cache emistr-api
docker compose up -d emistr-api
```

### Port 8000 je obsazený

Upravte v `docker-compose.yml`:
```yaml
ports:
  - "8080:8000"  # Změna externího portu na 8080
```

### Chyba připojení k databázi

Zkontrolujte `config.json` a ujistěte se, že databázové údaje jsou správné:
```bash
docker compose exec emistr-api cat /app/config/config.json
```

## 📚 Další informace

- **OpenAPI specifikace**: Dostupná na http://localhost:8000/openapi.json
- **Interaktivní dokumentace**: http://localhost:8000/docs (Swagger UI)
- **Alternativní dokumentace**: http://localhost:8000/redoc (ReDoc)

## 🔄 Architektura

```
┌─────────────┐
│   Web UI    │
└──────┬──────┘
       │ HTTP REST
       ▼
┌─────────────────────┐
│  FastAPI Adapter    │ (port 8000)
│  (api_adapter.py)   │
└──────┬──────────────┘
       │ in-process call
       ▼
┌─────────────────────┐
│   MCP Server        │
│   (server.py)       │
│  - DatabaseManager  │
│  - ResponseBuilder  │
│  - Anonymizer       │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│   MySQL Database    │
└─────────────────────┘
```

REST adaptér běží ve stejném procesu jako MCP server, sdílí databázový pool a všechny pomocné komponenty. Není potřeba spouštět dva samostatné procesy.
