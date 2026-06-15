import os
import time
from core.event_logger import log_event
from core.db import DB_PATH

SCREENSHOT_DIR = os.path.join(os.path.dirname(DB_PATH), "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


class BrowserController:
    def __init__(self, headless=True):
        from browser_use import Browser
        self._browser = Browser(headless=headless)
        self._page = None
        self._screenshot_count = 0

    async def start(self):
        self._page = await self._browser.get_current_page()
        log_event("browser_controller", "browser_action",
                  summary="Browser started", detail={"headless": self._browser.headless},
                  db_path=DB_PATH)

    async def goto(self, url):
        await self._page.goto(url, wait_until="domcontentloaded")
        await self._screenshot("goto_" + url.replace("https://", "").replace("/", "_")[:60])

    async def fill(self, selector, value):
        await self._page.fill(selector, value)

    async def click(self, selector):
        await self._page.click(selector)
        await self._page.wait_for_timeout(1000)

    async def wait_for_selector(self, selector, timeout=10000):
        await self._page.wait_for_selector(selector, timeout=timeout)

    async def text_content(self, selector):
        el = await self._page.query_selector(selector)
        return await el.inner_text() if el else ""

    async def is_visible(self, selector):
        el = await self._page.query_selector(selector)
        return el is not None and await el.is_visible()

    async def _screenshot(self, label=""):
        self._screenshot_count += 1
        path = os.path.join(SCREENSHOT_DIR, f"step_{self._screenshot_count:04d}_{label}.png")
        await self._page.screenshot(path=path)
        log_event("browser_controller", "browser_action",
                  summary=f"Screenshot: {label}",
                  detail={"screenshot": path, "url": self._page.url},
                  db_path=DB_PATH)
        return path

    async def close(self):
        if self._browser:
            await self._browser.close()
