from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def _now_utc():
    # SQLite stores naive datetimes; return naive UTC so comparisons work correctly.
    return datetime.now(timezone.utc).replace(tzinfo=None)
