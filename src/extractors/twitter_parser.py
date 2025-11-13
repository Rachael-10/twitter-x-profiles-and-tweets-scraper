import logging
from dataclasses import asdict
from typing import Any, Dict, Iterable, List, Optional

from .tweet_entities import normalize_tweet
from .utils_time import (
    normalize_to_utc,
    parse_date_input,
    parse_twitter_date,
)

logger = logging.getLogger(__name__)

class TwitterParser:
    """
    Parses raw tweet-like objects into a normalized representation and applies
    filtering rules on engagement and time range.
    """

    def __init__(
        self,
        min_likes: int = 0,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> None:
        self.min_likes = max(0, int(min_likes))

        self.since_dt = parse_date_input(since) if since else None
        self.until_dt = parse_date_input(until) if until else None

        if self.since_dt and self.until_dt and self.since_dt >= self.until_dt:
            logger.warning(
                "Since date (%s) is not earlier than until date (%s). "
                "Ignoring time range filter.",
                self.since_dt,
                self.until_dt,
            )
            self.since_dt = None
            self.until_dt = None

    def _passes_engagement_filters(self, tweet: Dict[str, Any]) -> bool:
        like_count = tweet.get("likeCount") or 0
        try:
            like_count = int(like_count)
        except (TypeError, ValueError):
            like_count = 0

        if like_count < self.min_likes:
            return False
        return True

    def _passes_time_filters(self, tweet: Dict[str, Any]) -> bool:
        if not self.since_dt and not self.until_dt:
            return True

        created_at_raw = tweet.get("createdAt")
        if not created_at_raw:
            # No createdAt; be conservative and filter out
            return False

        try:
            created_at = parse_twitter_date(created_at_raw)
            created_at_utc = normalize_to_utc(created_at)
        except ValueError:
            logger.debug("Failed to parse createdAt '%s'; dropping tweet.", created_at_raw)
            return False

        if self.since_dt:
            if created_at_utc < self.since_dt:
                return False

        if self.until_dt:
            if created_at_utc >= self.until_dt:
                return False

        return True

    def parse(self, records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize and filter a list of raw tweet records.

        :param records: Iterable of raw dict objects.
        :return: List of normalized tweet dicts.
        """
        normalized_tweets: List[Dict[str, Any]] = []

        for idx, raw in enumerate(records):
            if not isinstance(raw, dict):
                logger.debug("Skipping non-dict record at index %d: %r", idx, raw)
                continue

            try:
                normalized = normalize_tweet(raw)
                tweet_dict = asdict(normalized)
            except Exception as exc:  # pylint: disable=broad-except
                logger.exception("Failed to normalize record at index %d: %s", idx, exc)
                continue

            if not self._passes_engagement_filters(tweet_dict):
                logger.debug(
                    "Tweet %s filtered out by engagement (likes < %d).",
                    tweet_dict.get("id"),
                    self.min_likes,
                )
                continue

            if not self._passes_time_filters(tweet_dict):
                logger.debug(
                    "Tweet %s filtered out by time range (%s, %s).",
                    tweet_dict.get("id"),
                    self.since_dt,
                    self.until_dt,
                )
                continue

            normalized_tweets.append(tweet_dict)

        return normalized_tweets