import uuid
from typing import Dict, Any
from playwright.async_api import Playwright, Browser

async def launch_browser(
    playwright: Playwright,
    browsers: Dict[str, Browser],
    pages,
    defaults: Dict[str, Any],
    browser_type: str | None = None,
    headless: bool | None = None,
):
    bt = (browser_type or defaults.get("browser_type") or "chromium").lower()
    if bt not in ("chromium", "firefox", "webkit"):
        raise ValueError("Invalid browser_type. Use chromium|firefox|webkit.")
    hl = defaults.get("headless") if headless is None else headless
    browser: Browser = await getattr(playwright, bt).launch(headless=hl)
    bid = str(uuid.uuid4()); browsers[bid] = browser
    return {"browser_id": bid, "browser_type": bt, "headless": hl}

async def close_browser(
    playwright: Playwright,
    browsers: Dict[str, Browser],
    pages,
    defaults,
    browser_id: str,
):
    b = browsers.get(browser_id)
    if not b:
        raise ValueError("Browser not found")
    await b.close()
    del browsers[browser_id]
    return {"message": f"Browser {browser_id} closed"}
