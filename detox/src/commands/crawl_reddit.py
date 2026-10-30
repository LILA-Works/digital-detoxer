import asyncio

import click
from playwright.async_api import BrowserContext, Page

from detox.src import human
from detox.src.browser import launch_browser
from detox.src.vault import VaultError, fetch_credentials

REDDIT_URL = "https://www.reddit.com/"
LOGIN_URL = "https://www.reddit.com/login/"
LOGIN_TIMEOUT_MS = 180_000
REDDIT_SERVER = "reddit.com"


async def is_logged_in(context: BrowserContext) -> bool:
    """Reddit sets the `reddit_session` cookie only for authenticated sessions."""
    cookies = await context.cookies(REDDIT_URL)
    return any(c.get("name") == "reddit_session" for c in cookies)


async def log_in(page: Page, account: str) -> None:
    master = click.prompt("Vault master password", hide_input=True)
    try:
        creds = await asyncio.to_thread(fetch_credentials, REDDIT_SERVER, account, master)
    except VaultError as e:
        raise click.ClickException(str(e)) from e

    await human.pause(1.0, 2.5)
    await human.click(page, page.locator('input[name="username"]').first)
    await human.pause(0.3, 0.8)
    await human.type_text(page, creds.username)
    await human.pause(0.5, 1.2)
    await human.click(page, page.locator('input[name="password"]').first)
    await human.pause(0.3, 0.8)
    await human.type_text(page, creds.password)
    await human.pause(0.6, 1.5)
    await page.keyboard.press("Enter")


async def ensure_logged_in(context: BrowserContext, page: Page, account: str) -> None:
    await page.goto(REDDIT_URL)
    await human.pause(2.0, 4.0)
    if await is_logged_in(context):
        click.echo("Already logged in.")
        return

    click.echo("Not logged in. Going to the login page.")
    await human.idle_scroll(page)
    await page.goto(LOGIN_URL)
    await page.wait_for_selector('input[name="username"]')
    await log_in(page, account)

    click.echo(
        "Submitted credentials. If Reddit asks for 2FA or a CAPTCHA, complete it in the browser."
    )
    deadline = LOGIN_TIMEOUT_MS / 1000
    while deadline > 0 and not await is_logged_in(context):
        await asyncio.sleep(1)
        deadline -= 1
    if not await is_logged_in(context):
        raise click.ClickException("Login did not complete in time.")
    click.echo("Logged in.")
    await human.pause(2.0, 4.0)


@click.command("crawl-reddit")
@click.option("--account", required=True, help="Reddit username whose password is in the vault.")
@click.option("--keep-open", is_flag=True, help="Keep the browser open until you press a key.")
def crawl_reddit(account: str, keep_open: bool) -> None:
    """Open Reddit, log in via the vault if needed, then crawl."""

    async def run() -> None:
        async with launch_browser() as context:
            page = context.pages[0] if context.pages else await context.new_page()
            await ensure_logged_in(context, page, account)
            if keep_open:
                await asyncio.to_thread(click.pause, "Browser open. Press any key to close...")

    asyncio.run(run())
