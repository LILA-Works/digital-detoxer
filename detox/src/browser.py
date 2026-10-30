from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from playwright.async_api import BrowserContext, async_playwright

PROFILE_DIR = Path(".browser-profile")


@asynccontextmanager
async def launch_browser(headless: bool = False) -> AsyncGenerator[BrowserContext]:
    """Launch real Chrome with a persistent profile, configured to avoid bot detection.

    Uses the installed Chrome (not bundled Chromium), a headed window, and a persistent profile so
    cookies and logins survive across runs. Headless is detectable, so it is off by default.
    """
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            channel="chrome",
            headless=headless,
            no_viewport=True,
            ignore_default_args=["--enable-automation"],
            args=["--disable-blink-features=AutomationControlled"],
        )
        try:
            yield context
        finally:
            await context.close()
