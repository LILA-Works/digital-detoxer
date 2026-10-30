import asyncio
import random

from playwright.async_api import Locator, Page


async def pause(low: float = 0.4, high: float = 1.4) -> None:
    """Sleep a random, slightly right-skewed time, like a person reading or thinking."""
    await asyncio.sleep(min(high, random.triangular(low, high, low + (high - low) * 0.3)))


async def move_mouse(page: Page, x: float, y: float) -> None:
    """Move the mouse along a curved, jittery path with variable speed."""
    start_x, start_y = getattr(
        page, "_mouse_pos", (random.uniform(100, 600), random.uniform(100, 400))
    )
    steps = random.randint(18, 40)
    # A random control point bends the path into an arc instead of a straight line.
    ctrl_x = (start_x + x) / 2 + random.uniform(-120, 120)
    ctrl_y = (start_y + y) / 2 + random.uniform(-120, 120)
    for i in range(1, steps + 1):
        t = i / steps
        t = t * t * (3 - 2 * t)  # ease in/out
        bx = (1 - t) ** 2 * start_x + 2 * (1 - t) * t * ctrl_x + t**2 * x
        by = (1 - t) ** 2 * start_y + 2 * (1 - t) * t * ctrl_y + t**2 * y
        await page.mouse.move(bx + random.uniform(-1.5, 1.5), by + random.uniform(-1.5, 1.5))
        await asyncio.sleep(random.uniform(0.004, 0.02))
    await page.mouse.move(x, y)
    setattr(page, "_mouse_pos", (x, y))


async def click(page: Page, target: Locator) -> None:
    """Move to a random point inside the element, hesitate, then click."""
    await target.scroll_into_view_if_needed()
    box = await target.bounding_box()
    if box is None:
        await target.click()
        return
    x = box["x"] + box["width"] * random.uniform(0.25, 0.75)
    y = box["y"] + box["height"] * random.uniform(0.3, 0.7)
    await move_mouse(page, x, y)
    await pause(0.08, 0.35)
    await page.mouse.down()
    await asyncio.sleep(random.uniform(0.04, 0.14))
    await page.mouse.up()


async def type_text(page: Page, text: str) -> None:
    """Type one key at a time with uneven rhythm, longer gaps after some keys, and rare pauses."""
    for char in text:
        await page.keyboard.type(char)
        delay = random.gauss(0.11, 0.04)
        if random.random() < 0.08:
            delay += random.uniform(0.25, 0.7)
        await asyncio.sleep(max(0.03, delay))


async def idle_scroll(page: Page) -> None:
    """Scroll a little, as if skimming the page."""
    for _ in range(random.randint(1, 3)):
        await page.mouse.wheel(0, random.uniform(120, 500))
        await pause(0.4, 1.2)
