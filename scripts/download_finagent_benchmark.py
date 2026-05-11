"""Download the FinAgent Benchmark dataset snapshot for local sampling.

This script downloads raw external source files into a gitignored directory.
Curated samples should be copied or transformed into tracked files separately.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from huggingface_hub import snapshot_download


DEFAULT_REPO_ID = "Guen/finagent-benchmark"
DEFAULT_LOCAL_DIR = "data/external/raw/finagent-benchmark"
DEFAULT_ALLOW_PATTERNS = (
    "*.json",
    "*.jsonl",
    "*.csv",
    "*.parquet",
    "*.md",
    "README*",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download a local raw snapshot of Guen/finagent-benchmark."
    )
    parser.add_argument(
        "--repo-id",
        default=DEFAULT_REPO_ID,
        help=f"Hugging Face dataset repo id. Defaults to {DEFAULT_REPO_ID}.",
    )
    parser.add_argument(
        "--local-dir",
        default=DEFAULT_LOCAL_DIR,
        help=f"Local output directory. Defaults to {DEFAULT_LOCAL_DIR}.",
    )
    parser.add_argument(
        "--all-files",
        action="store_true",
        help="Download all files instead of only common data and README files.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=8,
        help="Number of download workers. Defaults to 8.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    local_dir = Path(args.local_dir)
    local_dir.mkdir(parents=True, exist_ok=True)

    allow_patterns = None if args.all_files else list(DEFAULT_ALLOW_PATTERNS)

    downloaded_path = snapshot_download(
        repo_id=args.repo_id,
        repo_type="dataset",
        local_dir=str(local_dir),
        allow_patterns=allow_patterns,
        max_workers=args.max_workers,
    )

    print(downloaded_path)


if __name__ == "__main__":
    main()
