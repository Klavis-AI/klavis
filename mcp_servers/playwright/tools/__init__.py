from typing import Dict, Any, Awaitable, Callable
from playwright.async_api import Playwright, Browser, Page
from .browser import launch_browser, close_browser
from .page import new_page, close_page, go_to_url
from .actions import click_selector, fill_selector, get_text
from .media import take_screenshot

def register_tools(
    playwright: Playwright,
    browsers: Dict[str, Browser],
    pages: Dict[str, Page],
    defaults: Dict[str, Any],
) -> Dict[str, Callable[..., Awaitable[Dict[str, Any]]]]:
    """
    Build and return the tool registry for this MCP server.
    Each tool is wrapped so it always receives the shared state
    (playwright instance, browsers dict, pages dict, defaults).
    """
    def bind(fn):
        async def _inner(**kwargs):
            return await fn(
                playwright=playwright,
                browsers=browsers,
                pages=pages,
                defaults=defaults,
                **kwargs
            )
        return _inner

    return {
        # Browser management
        "launch_browser":  bind(launch_browser),
        "close_browser":   bind(close_browser),

        # Page management
        "new_page":        bind(new_page),
        "close_page":      bind(close_page),
        "go_to_url":       bind(go_to_url),

        # Page actions
        "click_selector":  bind(click_selector),
        "fill_selector":   bind(fill_selector),
        "get_text":        bind(get_text),

        # Media
        "take_screenshot": bind(take_screenshot),
    }
