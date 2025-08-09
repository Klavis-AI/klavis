import base64
import uuid
from fastapi import FastAPI, HTTPException, Request
from playwright.async_api import async_playwright, Playwright, Browser, Page

app = FastAPI()

# Global Playwright instance and dictionaries to store browsers and pages
playwright_instance: Playwright | None = None
browsers: dict[str, Browser] = {}
pages: dict[str, Page] = {}

@app.get("/")
async def root():
    """Root endpoint for simple server check."""
    return {"message": "Playwright MCP Server is running"}

@app.get("/health")
async def health():
    """Health check endpoint to verify server status."""
    return {"status": "ok"}

@app.on_event("startup")
async def startup():
    """Start Playwright instance on server startup."""
    global playwright_instance
    playwright_instance = await async_playwright().start()
    print("Playwright started")

@app.on_event("shutdown")
async def shutdown():
    """Close all browsers and stop Playwright on server shutdown."""
    global playwright_instance
    for browser in list(browsers.values()):
        try:
            await browser.close()
        except Exception:
            pass
    if playwright_instance:
        await playwright_instance.stop()
    print("Playwright stopped")

@app.post("/launch_browser")
async def launch_browser(request: Request):
    """Launch a new browser instance of the specified type."""
    data = await request.json()
    browser_type = data.get("browserType") or data.get("browser_type")
    if browser_type not in ["chromium", "firefox", "webkit"]:
        raise HTTPException(status_code=400, detail="Invalid browser type. Must be chromium, firefox, or webkit.")
    try:
        browser = await getattr(playwright_instance, browser_type).launch(headless=True)
        browser_id = str(uuid.uuid4())
        browsers[browser_id] = browser
        return {"browser_id": browser_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to launch browser: {e}")

@app.post("/tools/call")
async def tools_call(request: Request):
    """
    Main endpoint to handle all tool actions:
    close_browser, new_page, close_page,
    go_to_url, click_selector, fill_selector,
    take_screenshot, get_text.
    """
    data = await request.json()
    name = data.get("name")
    arguments = data.get("arguments", {})

    # Close browser
    if name == "close_browser":
        browser_id = arguments.get("browser_id")
        browser = browsers.get(browser_id)
        if not browser:
            raise HTTPException(status_code=404, detail="Browser not found")
        try:
            await browser.close()
            del browsers[browser_id]
            return {"message": f"Browser {browser_id} closed"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to close browser: {e}")

    # Create new page
    if name == "new_page":
        browser_id = arguments.get("browser_id")
        browser = browsers.get(browser_id)
        if not browser:
            raise HTTPException(status_code=404, detail="Browser not found")
        try:
            page = await browser.new_page()
            page_id = str(uuid.uuid4())
            pages[page_id] = page
            return {"page_id": page_id}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create new page: {e}")

    # Close page
    if name == "close_page":
        page_id = arguments.get("page_id")
        page = pages.get(page_id)
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        try:
            await page.close()
            del pages[page_id]
            return {"message": f"Page {page_id} closed"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to close page: {e}")

    # Navigate to URL
    if name == "go_to_url":
        page_id = arguments.get("page_id")
        url = arguments.get("url")
        page = pages.get(page_id)
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        if not url:
            raise HTTPException(status_code=400, detail="Missing URL argument")
        try:
            # Wait for full page load with 60s timeout
            await page.goto(url, wait_until="load", timeout=60000)
            return {"message": f"Navigated to {url}"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to navigate: {e}")

    # Click an element by selector
    if name == "click_selector":
        page_id = arguments.get("page_id")
        selector = arguments.get("selector")
        page = pages.get(page_id)
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        if not selector:
            raise HTTPException(status_code=400, detail="Missing selector argument")
        try:
            await page.click(selector)
            return {"message": f"Clicked element {selector}"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to click element: {e}")

    # Fill input field
    if name == "fill_selector":
        page_id = arguments.get("page_id")
        selector = arguments.get("selector")
        text = arguments.get("text")
        page = pages.get(page_id)
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        if not selector or text is None:
            raise HTTPException(status_code=400, detail="Missing selector or text argument")
        try:
            # Wait for element to be present before filling
            await page.wait_for_selector(selector, timeout=10000)
            await page.fill(selector, text)
            return {"message": f"Filled element {selector} with text"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fill element: {e}")

    # Take screenshot
    if name == "take_screenshot":
        page_id = arguments.get("page_id")
        page = pages.get(page_id)
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        try:
            screenshot_bytes = await page.screenshot()
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
            return {"screenshot_base64": screenshot_b64}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to take screenshot: {e}")

    # Get text content of an element
    if name == "get_text":
        page_id = arguments.get("page_id")
        selector = arguments.get("selector")
        page = pages.get(page_id)
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        if not selector:
            raise HTTPException(status_code=400, detail="Missing selector argument")
        element = await page.query_selector(selector)
        if not element:
            raise HTTPException(status_code=404, detail="Element not found")
        try:
            text = await element.text_content()
            return {"text": text}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get text: {e}")

    # Unknown tool name handler
    raise HTTPException(status_code=400, detail=f"Unknown tool name: {name}")
