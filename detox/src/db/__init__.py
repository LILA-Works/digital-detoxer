from pathlib import Path

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlmodel import create_engine

DB_DIR = Path(".data/reddit")
DB_PATH = DB_DIR / "reddit.db"
DB_URL = f"sqlite:///{DB_PATH}"


def get_engine() -> Engine:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    engine = create_engine(DB_URL)

    # SQLite ignores foreign keys unless this is enabled on every connection.
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    return engine
