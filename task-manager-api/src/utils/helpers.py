import re
from datetime import datetime, timezone

EMAIL_RE = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')

VALID_TASK_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
VALID_ROLES = ('user', 'admin', 'manager')


def format_date(date_obj):
    return str(date_obj) if date_obj else None


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def is_valid_color(color):
    return bool(color and len(color) == 7 and color[0] == '#')
