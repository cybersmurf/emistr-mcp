# 1. Základní image
FROM python:3.11-slim

# 2. Nastavení pracovního adresáře
WORKDIR /app

# 3. Kopírování a instalace závislostí
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Vytvoření složky pro konfiguraci a kopírování souboru
RUN mkdir /app/config
COPY config.json /app/config/

# 5. Kopírování souborů aplikace
COPY . .

# 6. Spouštěcí příkaz
CMD ["python", "server.py"]