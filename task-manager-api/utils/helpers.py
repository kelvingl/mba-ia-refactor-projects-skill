from datetime import datetime, timezone
import re

_EMAIL_RE = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')


def now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def parse_date(date_string):
    for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    return None


def validate_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(email))


def is_valid_color(color: str) -> bool:
    return bool(color and len(color) == 7 and color[0] == '#')


def calculate_percentage(part: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round((part / total) * 100, 2)
