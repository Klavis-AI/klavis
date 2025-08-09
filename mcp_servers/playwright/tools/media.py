import base64
from typing import Dict, Any
from playwright.async_api import Playwright, Browser, Page

async def take_screenshot(
    playwright: Playwright,
    browsers: Dict[str, Browser],
    pages: Dict[str, Page],
    defaults,
    page_id: str,
    full_page: bool = False,
):
    p = pages.get(page_id)
    if not p:
        raise ValueError("Page not found")
    png = await p.screenshot(full_page=full_page)
    b64 = base64.b64encode(png).decode("utf-8")
    return {"screenshot_base64": b64}
