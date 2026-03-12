FROM python:3.12-slim-bookworm

WORKDIR /app

COPY mcp_servers/scholarly_toolathlon/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_servers/scholarly_toolathlon/src/ src/

ENV PYTHONPATH=/app/src

ENTRYPOINT ["python", "-c", "from mcp_scholarly import main; main()"]
