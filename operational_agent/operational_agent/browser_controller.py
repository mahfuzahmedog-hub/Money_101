import os
import asyncio
from playwright.async_api import async_playwright
from core.event_logger import log_event
from core.db import DB_PATH

SCREENSHOT_DIR = os.path.join(os.path.dirname(DB_PATH or "agent_data.db"), "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


class BrowserController:
    def __init__(self, headless=True):
        self._headless = headless
        self._playwright = None
        self._browser = None
        self._page = None
        self._screenshot_count = 0

    async def start(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self._headless,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        self._page = await self._browser.new_page()
        log_event("browser_controller", "browser_action",
                  summary=f"Browser started (headless={self._headless})",
                  detail={"headless": self._headless},
                  db_path=DB_PATH)

    async def goto(self, url):
        await self._page.goto(url, wait_until="domcontentloaded")
        await self._screenshot("goto")

    async def fill(self, selector, value):
        try:
            el = await self._page.wait_for_selector(selector, timeout=5000)
            await el.fill(value)
        except Exception as e:
            log_event("browser_controller", "error",
                      summary=f"Failed to fill {selector}: {e}",
                      status="failure", db_path=DB_PATH)

    async def click(self, selector):
        try:
            el = await self._page.wait_for_selector(selector, timeout=5000)
            await el.click()
            await asyncio.sleep(1.5)
        except Exception as e:
            log_event("browser_controller", "error",
                      summary=f"Failed to click {selector}: {e}",
                      status="failure", db_path=DB_PATH)

    async def wait_for_timeout(self, ms):
        await asyncio.sleep(ms / 1000)

    async def is_visible(self, selector, timeout=3000):
        try:
            await self._page.wait_for_selector(selector, timeout=timeout)
            return True
        except:
            return False

    async def text_content(self, selector):
        try:
            el = await self._page.query_selector(selector)
            return await el.inner_text() if el else ""
        except:
            return ""

    async def current_url(self):
        return self._page.url

    async def _screenshot(self, label=""):
        self._screenshot_count += 1
        path = os.path.join(SCREENSHOT_DIR, f"step_{self._screenshot_count:04d}_{label}.png")
        await self._page.screenshot(path=path, full_page=True)
        log_event("browser_controller", "browser_action",
                  summary=f"Screenshot: {label}",
                  detail={"screenshot": path, "url": self._page.url},
                  db_path=DB_PATH)
        return path

    async def close(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
