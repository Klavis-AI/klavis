import uuid
from typing import Dict, Any
from playwright.async_api import Playwright, Browser, Page

async def new_page(
    playwright: Playwright,
    browsers: Dict[str, Browser],
    pages: Dict[str, Page],
    defaults: Dict[str, Any],
    browser_id: str,
):
    b = browsers.get(browser_id)
    if not b:
        raise ValueError("Browser not found")
    page = await b.new_page()
    pid = str(uuid.uuid4()); pages[pid] = page
    return {"page_id": pid}

async def close_page(
    playwright: Playwright,
    browsers: Dict[str, Browser],
    pages: Dict[str, Page],
    defaults,
    page_id: str,
):
    p = pages.get(page_id)
    if not p:
        raise ValueError("Page not found")
    await p.close()
    del pages[page_id]
    return {"message": f"Page {page_id} closed"}

async def go_to_url(
    playwright: Playwright,
    browsers: Dict[str, Browser],
    pages: Dict[str, Page],
    defaults,
    page_id: str,
    url: str,
    wait_until: str = "domcontentloaded",
    timeout_ms: int = 60000,
):
    if not url:
        raise ValueError("Missing 'url'")
    p = pages.get(page_id)
    if not p:
        raise ValueError("Page not found")
    await p.goto(url, wait_until=wait_until, timeout=timeout_ms)
    return {"message": f"Navigated to {url}"}
