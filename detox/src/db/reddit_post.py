import re
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class RedditPost(SQLModel, table=True):
    """Metadata about a crawled post. The post content itself is deliberately not stored."""

    __tablename__ = "reddit_posts"  # pyright: ignore[reportAssignmentType]

    id: int | None = Field(default=None, primary_key=True)
    title: str
    author: str
    url: str = Field(unique=True, index=True)
    # Reddit only exposes the net score (upvotes minus downvotes), not the two separately.
    score: int
    time_posted: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def post_id(self) -> str:
        return self.post_id_from_url(self.url)

    @staticmethod
    def post_id_from_url(url: str) -> str:
        """Reddit's own ID for the post, e.g. `1xa7d8r` from `.../comments/1xa7d8r/some_title/`."""
        match = re.search(r"/comments/([^/?#]+)", url)
        if match is None:
            raise ValueError(f"Not a Reddit post URL: {url}")
        return match.group(1)
