from pathlib import Path

from sqlmodel import create_engine

DB_DIR = Path(".data/reddit")
DB_PATH = DB_DIR / "reddit.db"
DB_URL = f"sqlite:///{DB_PATH}"


def get_engine():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return create_engine(DB_URL)
