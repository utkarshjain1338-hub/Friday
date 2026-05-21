import asyncio
import webbrowser
from urllib.parse import quote_plus
from loguru import logger

# Try to import playwright for advanced automation
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


def _normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


async def _run_playwright(url: str):
    """Run playwright to open a URL if available."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            await page.goto(url)
            # Give it some time so the user can see it, in a real implementation
            # we'd keep the session alive or attach to an existing session.
            await asyncio.sleep(5)
            await browser.close()
            return True
    except Exception as e:
        logger.warning(f"Playwright failed, falling back to webbrowser: {e}")
        return False


def _open_url(url: str) -> bool:
    """Helper to open URL using either Playwright (if in event loop) or webbrowser."""
    url = _normalize_url(url)
    
    # Try playwright if we are in an async context
    try:
        loop = asyncio.get_running_loop()
        if PLAYWRIGHT_AVAILABLE:
            # We don't want to block, so we create a task (fire and forget for this basic implementation)
            loop.create_task(_run_playwright(url))
            return True
    except RuntimeError:
        pass
        
    # Fallback
    webbrowser.open_new_tab(url)
    return True


def open_website(url: str) -> str:
    if not url:
        return "Please specify a website to open."
    _open_url(url)
    return f"Opening {url}."


def search_google(query: str) -> str:
    if not query:
        return "Please provide search terms for Google."
    url = f"https://www.google.com/search?q={quote_plus(query)}"
    _open_url(url)
    return f"Searching Google for '{query}'."


def open_youtube(query: str = None) -> str:
    if query:
        url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
        _open_url(url)
        return f"Searching YouTube for '{query}'."

    _open_url("https://www.youtube.com")
    return "Opening YouTube."
