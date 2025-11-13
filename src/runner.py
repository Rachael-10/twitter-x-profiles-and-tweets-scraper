import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from extractors.twitter_parser import TwitterParser
from outputs.exporters import export_to_csv, export_to_json

def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

def project_root() -> Path:
    # src/runner.py -> src -> project root
    return Path(__file__).resolve().parents[1]

def load_json_file(path: Path) -> Any:
    if not path.exists():
        logging.error("File not found: %s", path)
        raise SystemExit(1)
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error("Failed to parse JSON file %s: %s", path, e)
        raise SystemExit(1)

def load_config(root: Path, override_path: Optional[str]) -> Dict[str, Any]:
    if override_path:
        cfg_path = Path(override_path)
        if not cfg_path.is_absolute():
            cfg_path = root / cfg_path
    else:
        cfg_path = root / "src" / "config" / "settings.example.json"

    if not cfg_path.exists():
        logging.warning(
            "Config file not found at %s. Using built-in defaults.", cfg_path
        )
        return {
            "input_file": "data/sample.json",
            "output_json": "data/output.tweets.json",
            "output_csv": "data/output.tweets.csv",
            "min_likes": 0,
            "since": None,
            "until": None,
        }

    logging.debug("Loading configuration from %s", cfg_path)
    cfg = load_json_file(cfg_path)

    # Ensure required keys with sensible defaults
    cfg.setdefault("input_file", "data/sample.json")
    cfg.setdefault("output_json", "data/output.tweets.json")
    cfg.setdefault("output_csv", "data/output.tweets.csv")
    cfg.setdefault("min_likes", 0)
    cfg.setdefault("since", None)
    cfg.setdefault("until", None)

    return cfg

def resolve_path(root: Path, maybe_relative: str) -> Path:
    path = Path(maybe_relative)
    if not path.is_absolute():
        path = root / path
    return path

def parse_cli_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Twitter (X) Profiles and Tweets Scraper – "
            "process JSON tweet data into structured outputs."
        )
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to a JSON settings file. Defaults to src/config/settings.example.json",
    )
    parser.add_argument(
        "--input-json",
        type=str,
        help="Override input JSON file containing raw tweet objects.",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        help="Override path for normalized tweets JSON output.",
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        help="Override path for normalized tweets CSV output.",
    )
    parser.add_argument(
        "--min-likes",
        type=int,
        help="Filter tweets with fewer likes than this value.",
    )
    parser.add_argument(
        "--since",
        type=str,
        help="Only include tweets created at or after this date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--until",
        type=str,
        help="Only include tweets created before this date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--no-json",
        action="store_true",
        help="Disable JSON export.",
    )
    parser.add_argument(
        "--no-csv",
        action="store_true",
        help="Disable CSV export.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args(argv)

def main(argv: Optional[List[str]] = None) -> None:
    args = parse_cli_args(argv)
    setup_logging(args.verbose)

    root = project_root()
    logging.debug("Project root resolved to %s", root)

    cfg = load_config(root, args.config)

    input_file = args.input_json or cfg.get("input_file")
    output_json_path = args.output_json or cfg.get("output_json")
    output_csv_path = args.output_csv or cfg.get("output_csv")
    min_likes = (
        args.min_likes
        if args.min_likes is not None
        else int(cfg.get("min_likes", 0))
    )
    since = args.since or cfg.get("since")
    until = args.until or cfg.get("until")

    input_path = resolve_path(root, input_file)
    output_json_path_full = resolve_path(root, output_json_path)
    output_csv_path_full = resolve_path(root, output_csv_path)

    logging.info("Loading raw data from %s", input_path)
    raw_data = load_json_file(input_path)

    if not isinstance(raw_data, list):
        logging.error(
            "Expected top-level JSON array in %s, got %s",
            input_path,
            type(raw_data).__name__,
        )
        raise SystemExit(1)

    parser = TwitterParser(
        min_likes=min_likes,
        since=since,
        until=until,
    )

    logging.info(
        "Parsing %d records (min_likes=%d, since=%s, until=%s)",
        len(raw_data),
        min_likes,
        since,
        until,
    )
    normalized = parser.parse(raw_data)

    if not normalized:
        logging.warning("No tweets left after filtering.")
    else:
        logging.info("Parsed %d tweets.", len(normalized))

    exported_paths: List[Path] = []

    if not args.no_json:
        logging.info("Exporting %d tweets to JSON: %s", len(normalized), output_json_path_full)
        export_to_json(normalized, output_json_path_full)
        exported_paths.append(output_json_path_full)

    if not args.no_csv:
        logging.info("Exporting %d tweets to CSV: %s", len(normalized), output_csv_path_full)
        export_to_csv(normalized, output_csv_path_full)
        exported_paths.append(output_csv_path_full)

    logging.info("Done. Exported %d files.", len(exported_paths))
    for p in exported_paths:
        logging.info(" - %s", p)

    # Print a short human-readable summary to stdout
    print(
        json.dumps(
            {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "input_file": str(input_path),
                "tweets_processed": len(raw_data),
                "tweets_exported": len(normalized),
                "exports": [str(p) for p in exported_paths],
            },
            indent=2,
        )
    )

if __name__ == "__main__":
    main(sys.argv[1:])