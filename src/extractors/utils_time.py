from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

TWITTER_DATE_FORMAT = "%a %b %d %H:%M:%S %z %Y"  # Example: Thu Apr 28 00:56:58 +0000 2022

def parse_twitter_date(date_str: str) -> datetime:
    """
    Parse a Twitter-style date string or ISO-8601 string into a datetime.

    Raises ValueError if parsing fails.
    """
    if not date_str:
        raise ValueError("Empty date string")

    # Try Twitter's classic format first
    try:
        return datetime.strptime(date_str, TWITTER_DATE_FORMAT)
    except ValueError:
        pass

    # Try ISO-8601
    try:
        # fromisoformat supports many variants in Python 3.11+
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        pass

    raise ValueError(f"Unsupported date format: {date_str!r}")

def normalize_to_utc(dt: datetime) -> datetime:
    """
    Normalize any timezone-aware datetime to UTC. If naive, assume it's UTC.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def parse_date_input(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parse a simple date input (YYYY-MM-DD) to a UTC datetime at midnight.

    Returns None if date_str is None or empty.
    Raises ValueError if the input cannot be parsed.
    """
    if not date_str:
        return None

    date_str = date_str.strip()
    if not date_str:
        return None

    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.replace(tzinfo=timezone.utc)