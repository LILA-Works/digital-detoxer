import uuid
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class RedditSummary(SQLModel, table=True):
    """A generated summary of a crawled post, keyed by the post's URL."""

    __tablename__ = "reddit_summaries"  # pyright: ignore[reportAssignmentType]

    url: str = Field(foreign_key="reddit_posts.url", primary_key=True)
    summary: str
    update_id: uuid.UUID | None = Field(default=None, foreign_key="updates.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
