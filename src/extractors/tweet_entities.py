from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class Author:
    userName: str
    url: str
    id: str
    name: str
    followers: int = 0
    following: int = 0
    verified: bool = False
    location: Optional[str] = None
    bio: Optional[str] = None
    entities: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Tweet:
    type: str
    id: str
    url: str
    text: str
    retweetCount: int = 0
    replyCount: int = 0
    likeCount: int = 0
    quoteCount: int = 0
    bookmarkCount: int = 0
    createdAt: Optional[str] = None
    lang: Optional[str] = None
    media: List[Any] = field(default_factory=list)
    source: Optional[str] = None
    isReply: bool = False
    author: Author = field(default_factory=lambda: Author(
        userName="",
        url="",
        id="",
        name="",
    ))
    otherData: Dict[str, Any] = field(default_factory=dict)
    followers: int = 0
    following: int = 0
    entities: Dict[str, Any] = field(default_factory=dict)

def _safe_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    if isinstance(value, bool):
        return int(value)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return False

def normalize_author(raw_author: Dict[str, Any]) -> Author:
    return Author(
        userName=str(raw_author.get("userName") or raw_author.get("username") or ""),
        url=str(raw_author.get("url") or ""),
        id=str(raw_author.get("id") or ""),
        name=str(raw_author.get("name") or ""),
        followers=_safe_int(
            raw_author.get("followers") or raw_author.get("followersCount"), 0
        ),
        following=_safe_int(
            raw_author.get("following") or raw_author.get("followingCount"), 0
        ),
        verified=_safe_bool(raw_author.get("verified")),
        location=raw_author.get("location"),
        bio=raw_author.get("bio") or raw_author.get("description"),
        entities=raw_author.get("entities") or {},
    )

def normalize_tweet(raw: Dict[str, Any]) -> Tweet:
    """
    Convert a raw tweet-like dict (from Twitter API, HTML parser, or sample.json)
    into the internal Tweet dataclass.
    """
    raw_author = raw.get("author") or {}
    author = normalize_author(raw_author)

    # Collect non-canonical keys into otherData to avoid losing information
    canonical_keys = {
        "type",
        "id",
        "url",
        "text",
        "retweetCount",
        "replyCount",
        "likeCount",
        "quoteCount",
        "bookmarkCount",
        "createdAt",
        "lang",
        "media",
        "source",
        "isReply",
        "author",
        "followers",
        "following",
        "entities",
    }

    other_data: Dict[str, Any] = {}
    for key, value in raw.items():
        if key not in canonical_keys:
            other_data[key] = value

    tweet = Tweet(
        type=str(raw.get("type") or "tweet"),
        id=str(raw.get("id") or ""),
        url=str(raw.get("url") or ""),
        text=str(raw.get("text") or raw.get("full_text") or ""),
        retweetCount=_safe_int(raw.get("retweetCount") or raw.get("retweet_count"), 0),
        replyCount=_safe_int(raw.get("replyCount") or raw.get("reply_count"), 0),
        likeCount=_safe_int(raw.get("likeCount") or raw.get("favorite_count"), 0),
        quoteCount=_safe_int(raw.get("quoteCount") or raw.get("quote_count"), 0),
        bookmarkCount=_safe_int(raw.get("bookmarkCount") or raw.get("bookmark_count"), 0),
        createdAt=str(raw.get("createdAt") or raw.get("created_at") or ""),
        lang=raw.get("lang"),
        media=raw.get("media") or [],
        source=raw.get("source"),
        isReply=_safe_bool(
            raw.get("isReply")
            or raw.get("in_reply_to_status_id")
            or raw.get("in_reply_to_user_id")
        ),
        author=author,
        otherData=other_data,
        followers=author.followers,
        following=author.following,
        entities=author.entities,
    )

    return tweet