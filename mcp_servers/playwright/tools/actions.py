from typing import Dict, Any
from playwright.async_api import Playwright, Browser, Page

DEFAULT_TIMEOUT = 30000

async def click_selector(
    playwright: Playwright,
    browsers: Dict[str, Browser],
    pages: Dict[str, Page],
    defaults,
    page_id: str,
    selector: str,
    timeout_ms: int = DEFAULT_TIMEOUT,
):
    if not selector:
        raise ValueError("Missing 'selector'")
    p = pages.get(page_id)
    if not p:
        raise ValueError("Page not found")
    await p.wait_for_selector(selector, timeout=timeout_ms)
    await p.click(selector, timeout=timeout_ms)
    return {"message": f"Clicked {selector}"}

async def fill_selector(
    playwright: Playwright,
    browsers: Dict[str, Browser],
    pages: Dict[str, Page],
    defaults,
    page_id: str,
    selector: str,
    text: str,
    timeout_ms: int = DEFAULT_TIMEOUT,
):
    if not selector:
        raise ValueError("Missing 'selector'")
    p = pages.get(page_id)
    if not p:
        raise ValueError("Page not found")
    await p.wait_for_selector(selector, timeout=timeout_ms)
    await p.fill(selector, text, timeout=timeout_ms)
    return {"message": f"Filled {selector}"}

async def get_text(
    playwright: Playwright,
    browsers: Dict[str, Browser],
    pages: Dict[str, Page],
    defaults,
    page_id: str,
    selector: str,
    timeout_ms: int = DEFAULT_TIMEOUT,
):
    if not selector:
        raise ValueError("Missing 'selector'")
    p = pages.get(page_id)
    if not p:
        raise ValueError("Page not found")
    await p.wait_for_selector(selector, timeout=timeout_ms)
    el = await p.query_selector(selector)
    if not el:
        raise ValueError("Element not found")
    text = (await el.text_content()) or ""
    return {"text": text}
