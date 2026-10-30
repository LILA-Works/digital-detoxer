import asyncio

import click

from detox.src.browser import launch_browser


@click.group()
def main() -> None:
    """Digital detoxer."""


@main.command("test-browser")
@click.option("--url", default="https://bot.sannysoft.com", show_default=True)
@click.option("--headless", is_flag=True, help="Run headless (easier to detect as a bot).")
@click.option("--keep-open", is_flag=True, help="Keep the browser open until you press a key.")
def test_browser(url: str, headless: bool, keep_open: bool) -> None:
    """Open a bot-detection test page and report whether automation is visible."""

    async def run() -> None:
        async with launch_browser(headless=headless) as context:
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto(url)
            webdriver = await page.evaluate("navigator.webdriver")
            click.echo(f"navigator.webdriver = {webdriver}")
            if keep_open:
                await asyncio.to_thread(click.pause, "Browser open. Press any key to close...")
            else:
                await page.wait_for_timeout(3000)

    asyncio.run(run())


if __name__ == "__main__":
    main()
