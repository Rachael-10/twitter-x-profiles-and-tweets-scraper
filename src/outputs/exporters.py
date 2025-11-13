import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List

logger = logging.getLogger(__name__)

def export_to_json(records: Iterable[Dict[str, Any]], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Convert iterable to list to allow length checks elsewhere
    data = list(records)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.debug("Wrote %d records to JSON: %s", len(data), path)
    return path

def _flatten_tweet(tweet: Dict[str, Any]) -> Dict[str, Any]:
    flat: Dict[str, Any] = dict(tweet)

    author = flat.pop("author", {}) or {}
    if not isinstance(author, dict):
        author = {}

    for key, value in author.items():
        flat[f"author_{key}"] = value

    # Serialize complex fields as JSON strings for CSV compatibility
    for key in ("media", "otherData", "entities"):
        if key in flat:
            flat[key] = json.dumps(flat[key], ensure_ascii=False)

    return flat

def export_to_csv(records: Iterable[Dict[str, Any]], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    data: List[Dict[str, Any]] = [_flatten_tweet(r) for r in records]

    if not data:
        # Always create an empty CSV with no rows to signal that export ran
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([])
        logger.debug("No records to export; created empty CSV at %s", path)
        return path

    fieldnames = sorted(data[0].keys())

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

    logger.debug("Wrote %d records to CSV: %s", len(data), path)
    return path