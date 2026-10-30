import json

import click
from sqlmodel import Session, col, select

from detox.src.commands.crawl_reddit import POSTS_DIR
from detox.src.db import get_engine
from detox.src.db.reddit_post import RedditPost
from detox.src.db.reddit_summary import RedditSummary
from detox.src.db.update import Update
from detox.src.llm import ask
from detox.src.notify import notify

POSTS_TO_SUMMARIZE = 5
SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {"summary": {"type": "string"}},
    "required": ["summary"],
}
CLASSIFY_SCHEMA = {
    "type": "object",
    "properties": {"interesting": {"type": "boolean"}},
    "required": ["interesting"],
}
UPDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "message": {
            "type": "string",
            "description": "A single sentence of at most 30 words, with no preamble or label.",
        }
    },
    "required": ["message"],
}
# Placeholder criteria for the classifier. Edit to taste.
INTEREST_CRITERIA = "Anything related to investing, companies, markets or the economy."

SUMMARIZE_PROMPT = """Summarize this Reddit post and its top comments in ONE sentence.

{content}"""

CLASSIFY_PROMPT = """Decide whether the reader would be interested in this Reddit post summary.

Criteria for interest: {criteria}

Summary: {summary}"""

UPDATE_PROMPT = """Below are summaries of recent Reddit posts. Write a single sentence of at most \
30 words saying what people are talking about, covering the main themes. Start directly with the \
content, without an introduction like "Users are discussing" or a label.

{summaries}"""


def post_content(post: RedditPost) -> str:
    """Title, body and top comments from the raw crawl data, falling back to the title alone."""
    path = POSTS_DIR / f"{post.post_id}.json"
    if not path.exists():
        return f"Title: {post.title}"
    raw = json.loads(path.read_text())
    parts = [f"Title: {raw['title']}"]
    if raw.get("selftext"):
        parts.append(f"Body: {raw['selftext']}")
    for comment in raw.get("comments", []):
        if comment.get("body"):
            parts.append(f"Comment: {comment['body']}")
    return "\n\n".join(parts)


def summarize_posts(limit: int = POSTS_TO_SUMMARIZE, overwrite: bool = False) -> int:
    """Summarize the latest posts and store the summaries.

    Only posts without a summary are considered, unless `overwrite` is set, in which case the
    latest posts are summarized again and their existing summaries replaced.
    """
    with Session(get_engine()) as session:
        query = select(RedditPost)
        if not overwrite:
            query = query.where(col(RedditPost.url).not_in(select(RedditSummary.url)))
        posts = session.exec(
            query.order_by(col(RedditPost.time_posted).desc(), col(RedditPost.id).desc()).limit(
                limit
            )
        ).all()
        for post in posts:
            text = ask(SUMMARIZE_PROMPT.format(content=post_content(post)), SUMMARY_SCHEMA)[
                "summary"
            ]
            # Keeps update_id, so a regenerated summary isn't delivered a second time.
            existing = session.get(RedditSummary, post.url)
            if existing is None:
                session.add(RedditSummary(url=post.url, summary=text))
            else:
                existing.summary = text
                session.add(existing)
            session.commit()
            click.echo(f"  {post.title[:60]} -> {text}")
        return len(posts)


def is_interesting(summary: str) -> bool:
    """Placeholder classifier: asks the LLM whether the summary matches INTEREST_CRITERIA."""
    prompt = CLASSIFY_PROMPT.format(criteria=INTEREST_CRITERIA, summary=summary)
    return bool(ask(prompt, CLASSIFY_SCHEMA, max_tokens=20)["interesting"])


def create_update() -> Update | None:
    """Classify summaries not yet in an update, then summarize the interesting ones into one."""
    with Session(get_engine()) as session:
        pending = session.exec(
            select(RedditSummary)
            .where(col(RedditSummary.update_id).is_(None))
            .order_by(col(RedditSummary.created_at))
        ).all()
        interesting = [s for s in pending if is_interesting(s.summary)]
        click.echo(f"  {len(interesting)} of {len(pending)} summaries are of interest")
        if not interesting:
            return None

        bullets = "\n".join(f"- {s.summary}" for s in interesting)
        update = Update(
            message=ask(UPDATE_PROMPT.format(summaries=bullets), UPDATE_SCHEMA)["message"]
        )
        session.add(update)
        # No ORM relationship ties the tables together, so the update row has to exist before
        # the summaries that reference it are written.
        session.flush()
        for summary in interesting:
            summary.update_id = update.id
            session.add(summary)
        session.commit()
        session.refresh(update)
        return update


@click.command("summarize-reddit")
@click.option(
    "--resummarize",
    is_flag=True,
    help="Overwrite the summaries of the latest posts instead of only summarizing new ones.",
)
@click.option("--no-notify", is_flag=True, help="Create the update without sending a notification.")
def summarize_reddit(no_notify: bool, resummarize: bool) -> None:
    """Summarize new posts, then bundle the interesting summaries into a notified update."""
    click.echo("Summarizing posts")
    click.echo(f"Summarized {summarize_posts(overwrite=resummarize)} posts")
    click.echo("Creating update")
    update = create_update()
    if update is None:
        click.echo("Nothing new of interest, no update created.")
        return
    if no_notify:
        click.echo(f"Created update (notification skipped): {update.message}")
    else:
        notify(update.message)
