FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip

COPY mcp_servers/cal_com/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_servers/cal_com/server.py .
COPY mcp_servers/cal_com/tools/ ./tools/

EXPOSE 5000

CMD ["python", "-u", "server.py"]
