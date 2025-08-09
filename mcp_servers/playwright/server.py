import os, json, asyncio
from typing import Any, Dict, Callable, Awaitable
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel, Field
from playwright.async_api import async_playwright, Playwright, Browser, Page
from .tools import register_tools

app = FastAPI(title="Playwright MCP Server", version="1.0.0")

playwright: Playwright | None = None
browsers: Dict[str, Browser] = {}
pages: Dict[str, Page] = {}

HEADLESS_DEFAULT = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() in ("1","true","yes")
BROWSER_DEFAULT  = os.getenv("PLAYWRIGHT_BROWSER", "chromium")

class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)

TOOL_REGISTRY: Dict[str, Callable[..., Awaitable[Dict[str, Any]]]] = {}

@app.on_event("startup")
async def _startup():
    global playwright, TOOL_REGISTRY
    playwright = await async_playwright().start()
    TOOL_REGISTRY = register_tools(
        playwright=playwright,
        browsers=browsers,
        pages=pages,
        defaults={"headless": HEADLESS_DEFAULT, "browser_type": BROWSER_DEFAULT},
    )

@app.on_event("shutdown")
async def _shutdown():
    global playwright
    for b in list(browsers.values()):
        try:
            await b.close()
        except Exception:
            pass
    browsers.clear(); pages.clear()
    if playwright:
        await playwright.stop()

@app.get("/health")
async def health():
    return {"status":"ok"}

@app.get("/tools")
async def list_tools():
    return {"tools": sorted(list(TOOL_REGISTRY.keys()))}

@app.post("/mcp")
async def mcp_call(call: ToolCall):
    if call.name not in TOOL_REGISTRY:
        raise HTTPException(400, f"Unknown tool name: {call.name}")
    try:
        result = await TOOL_REGISTRY[call.name](**call.arguments)
        return JSONResponse({"ok": True, "data": result})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/sse")
async def sse():
    async def gen():
        while True:
            yield {"event":"heartbeat","data":json.dumps({"ok":True})}
            await asyncio.sleep(15)
    return EventSourceResponse(gen())

@app.get("/")
async def root():
    return {"message":"Playwright MCP Server is running"}
