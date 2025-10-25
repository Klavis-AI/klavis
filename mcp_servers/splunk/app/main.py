from fastapi import FastAPI
from app.tools import search_logs, get_events, trigger_alert

app = FastAPI(
    title="Splunk MCP Server for Klavis AI",
    description="Atomic tools for querying Splunk and managing events, for AI agent integration."
)

app.include_router(search_logs.router)
app.include_router(get_events.router)
app.include_router(trigger_alert.router)

@app.get("/")
async def root():
    return {"message": "Splunk MCP Server running!"}
