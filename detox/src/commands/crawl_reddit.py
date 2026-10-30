import asyncio
import json
import re
from datetime import datetime
from pathlib import Path

import click
from playwright.async_api import BrowserContext, Locator, Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from detox.src import human
from detox.src.browser import launch_browser
from detox.src.commands.utils.unlock import with_vault
from detox.src.vault import fetch_credentials

SUBREDDITS: list[str] = [
    "https://www.reddit.com/r/ValueInvesting/",
]
POSTS_PER_SUBREDDIT = 10
COMMENTS_PER_POST = 10
OUTPUT_DIR = Path(".data/reddit")

REDDIT_URL = "https://www.reddit.com/"
LOGIN_URL = "https://www.reddit.com/login/"
LOGIN_TIMEOUT_MS = 180_000
REDDIT_SERVER = "reddit.com"


async def is_logged_in(context: BrowserContext) -> bool:
    """Reddit sets the `reddit_session` cookie only for authenticated sessions."""
    cookies = await context.cookies(REDDIT_URL)
    return any(c.get("name") == "reddit_session" for c in cookies)


async def log_in(page: Page, account: str) -> None:
    creds = await asyncio.to_thread(
        with_vault, lambda master: fetch_credentials(REDDIT_SERVER, account, master)
    )

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


def subreddit_name(url: str) -> str:
    match = re.search(r"/r/([^/?#]+)", url)
    if match is None:
        raise click.ClickException(f"Not a subreddit URL: {url}")
    return match.group(1)


POST_SELECTOR = "shreddit-post"
TOP_LEVEL_COMMENT_SELECTOR = 'shreddit-comment[depth="0"]'
POST_LINK_SELECTOR = 'a[slot="title"], a[slot="full-post-link"]'
MAX_SCROLLS = 8

# Runs in the page against one `shreddit-post` on a listing.
POST_SUMMARY_JS = """e => ({
    title: e.getAttribute('post-title'),
    author: e.getAttribute('author'),
    score: Number(e.getAttribute('score')),
    permalink: e.getAttribute('permalink'),
})"""

# Runs in the page against the `shreddit-post` of the post being viewed.
POST_DETAIL_JS = """e => ({
    selftext: e.querySelector('[slot="text-body"]')?.innerText ?? null,
    external_url: e.getAttribute('content-href'),
})"""

# Runs in the page against one `shreddit-comment`.
COMMENT_JS = """e => ({
    author: e.getAttribute('author'),
    score: Number(e.getAttribute('score')),
    body: e.querySelector('[slot="comment"]')?.innerText ?? null,
    permalink: e.getAttribute('permalink'),
})"""


def absolute(path: str | None) -> str | None:
    return f"{REDDIT_URL.rstrip('/')}{path}" if path and path.startswith("/") else path


async def scroll_until(page: Page, selector: str, count: int) -> None:
    """Scroll like a reader until at least `count` elements match, or give up."""
    for _ in range(MAX_SCROLLS):
        if await page.locator(selector).count() >= count:
            return
        await human.idle_scroll(page)


async def sort_by_top(page: Page) -> None:
    """Pick "Top" in the comment sort menu. Best effort: the default order is a fine fallback."""
    try:
        await human.click(page, page.get_by_role("button", name=re.compile("sort", re.I)).first)
        await human.pause(0.4, 1.0)
        await human.click(page, page.get_by_role("menuitem", name="Top", exact=True).first)
        await human.pause(1.5, 3.0)
    except PlaywrightTimeoutError:
        click.echo("  could not open the comment sort menu, using the default order.", err=True)


async def read_comments(page: Page) -> list[dict]:
    """Scroll to each top-level comment in turn, dwell on it, and read it."""
    await scroll_until(page, TOP_LEVEL_COMMENT_SELECTOR, COMMENTS_PER_POST)
    comments = page.locator(TOP_LEVEL_COMMENT_SELECTOR)
    read = []
    for i in range(min(await comments.count(), COMMENTS_PER_POST)):
        comment = comments.nth(i)
        await human.scroll_to(page, comment)
        data = await comment.evaluate(COMMENT_JS)
        await human.pause(*human.reading_time(data["body"]))
        data["url"] = absolute(data.pop("permalink"))
        read.append(data)
    return sorted(read, key=lambda c: c["score"], reverse=True)


async def crawl_post(page: Page, post: Locator) -> dict:
    """Click into a post, read it and its top comments, then go back to the listing."""
    summary = await post.evaluate(POST_SUMMARY_JS)
    click.echo(f"  {(summary['title'] or '')[:70]}")
    result = {
        "title": summary["title"],
        "author": summary["author"],
        "score": summary["score"],
        "url": absolute(summary["permalink"]),
        "selftext": None,
        "external_url": None,
        "comments": [],
    }
    await human.scroll_to(page, post)
    await human.pause(0.6, 1.8)
    await human.click(page, post.locator(POST_LINK_SELECTOR).first)
    try:
        await page.wait_for_url("**/comments/**", timeout=15_000)
        await page.wait_for_selector(POST_SELECTOR, timeout=15_000)
    except PlaywrightTimeoutError:
        click.echo(f"  post did not open, skipping: {result['url']}", err=True)
        return result
    await human.pause(1.5, 3.5)

    opened = page.locator(POST_SELECTOR).first
    await human.scroll_to(page, opened)
    result.update(await opened.evaluate(POST_DETAIL_JS))
    await human.pause(*human.reading_time(result["selftext"]))

    await sort_by_top(page)
    result["comments"] = (await read_comments(page))[:COMMENTS_PER_POST]
    return result


async def go_back_to_listing(page: Page) -> None:
    """Use the browser's back button and wait for the listing to render again."""
    await human.pause(0.8, 2.0)
    await page.go_back()
    await page.wait_for_selector(POST_SELECTOR, timeout=15_000)
    await human.pause(1.0, 2.5)


async def crawl_subreddit(page: Page, url: str) -> dict:
    name = subreddit_name(url)
    click.echo(f"Crawling r/{name}")
    await human.pause(2.0, 5.0)
    await page.goto(f"{REDDIT_URL}r/{name}/")
    try:
        await page.wait_for_selector(POST_SELECTOR, timeout=15_000)
    except PlaywrightTimeoutError:
        click.echo(f"  no posts found for r/{name}, skipping.", err=True)
        return {"subreddit": name, "url": url, "posts": []}
    await human.pause(1.5, 3.5)

    posts = []
    for i in range(POSTS_PER_SUBREDDIT):
        await scroll_until(page, POST_SELECTOR, i + 1)
        listing = page.locator(POST_SELECTOR)
        if await listing.count() <= i:
            break
        post = listing.nth(i)
        posts.append(await crawl_post(page, post))
        if i < POSTS_PER_SUBREDDIT - 1:
            await go_back_to_listing(page)
    return {"subreddit": name, "url": url, "posts": posts}


async def crawl(page: Page) -> Path:
    results = [await crawl_subreddit(page, url) for url in SUBREDDITS]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"crawl-{datetime.now():%Y%m%d-%H%M%S}.json"
    path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    return path


@click.command("crawl-reddit")
@click.option("--account", required=True, help="Reddit username whose password is in the vault.")
@click.option("--keep-open", is_flag=True, help="Keep the browser open until you press a key.")
def crawl_reddit(account: str, keep_open: bool) -> None:
    """Open Reddit, log in via the vault if needed, then crawl the configured subreddits."""
    if not SUBREDDITS:
        raise click.ClickException("SUBREDDITS is empty. Add URLs at the top of the file.")

    async def run() -> None:
        async with launch_browser() as context:
            page = context.pages[0] if context.pages else await context.new_page()
            await ensure_logged_in(context, page, account)
            path = await crawl(page)
            click.echo(f"Saved {path}")
            if keep_open:
                await asyncio.to_thread(click.pause, "Browser open. Press any key to close...")

    asyncio.run(run())
