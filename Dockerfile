FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /app/config
COPY config.json /app/config/config.json
COPY . .
EXPOSE 9201
CMD ["python", "server.py"]
