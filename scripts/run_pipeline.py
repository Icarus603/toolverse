#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simple pipeline to run crawlers and update data.

This script orchestrates the following steps:
1. Run crawlers to fetch raw data.
2. Merge raw data into processed YAML database.
3. Update README with latest tools.
4. Ensure contributor section exists.

It can be executed manually or by a scheduled job.
"""

import argparse
import subprocess
import os
import logging
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent

CRAWLERS_DIR = SCRIPT_DIR / "crawlers"
PROCESSORS_DIR = SCRIPT_DIR / "processors"
UPDATERS_DIR = SCRIPT_DIR / "updaters"


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def run_cmd(cmd):
    """Run a command and exit on failure."""
    logging.info("Running: %s", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def ensure_directories():
    """Create required data directories if they are missing."""
    (ROOT_DIR / "data" / "raw" / "huggingface").mkdir(parents=True, exist_ok=True)
    (ROOT_DIR / "data" / "raw" / "reddit").mkdir(parents=True, exist_ok=True)
    (ROOT_DIR / "data" / "processed" / "tools_archive").mkdir(parents=True, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Run Toolverse update pipeline")
    parser.add_argument("--skip-crawlers", action="store_true", help="Skip running crawlers")
    parser.add_argument("--hf-pages", type=int, default=1, help="Pages to crawl from HuggingFace")
    parser.add_argument("--reddit-limit", type=int, default=10, help="Number of posts per subreddit")
    parser.add_argument("--days", type=int, default=7, help="Days of raw files to process")
    args = parser.parse_args()

    ensure_directories()

    if not args.skip_crawlers:
        run_cmd([
            "python",
            str(CRAWLERS_DIR / "huggingface_crawler.py"),
            "--max-pages",
            str(args.hf_pages),
        ])

        reddit_env_set = all(
            os.getenv(var) for var in ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"]
        )
        if reddit_env_set:
            run_cmd([
                "python",
                str(CRAWLERS_DIR / "reddit_crawler.py"),
                "--client_id",
                os.getenv("REDDIT_CLIENT_ID"),
                "--client_secret",
                os.getenv("REDDIT_CLIENT_SECRET"),
                "--limit",
                str(args.reddit_limit),
            ])
        else:
            logging.warning("Reddit credentials not set, skipping reddit crawler")

    run_cmd([
        "python",
        str(PROCESSORS_DIR / "update_yaml.py"),
        "--days",
        str(args.days),
    ])

    run_cmd(["python", str(UPDATERS_DIR / "update_readme.py")])
    run_cmd(["python", str(UPDATERS_DIR / "update_contributors.py")])


if __name__ == "__main__":
    main()
