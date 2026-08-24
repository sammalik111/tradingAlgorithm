"""Run the nightly-scrape job on demand against LocalStack. Local dev only
-- see documentation/workers.md.

Usage:
    docker compose exec workers python local/run_nightly_scrape.py
    docker compose exec workers python local/run_nightly_scrape.py --include-all-history
"""

import argparse
import json

from trading_workers.jobs.nightly_scrape import handler


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--include-all-history",
        action="store_true",
        help="Bypass the 45-day recency filter (see run_nightly_scrape's docstring).",
    )
    args = parser.parse_args()

    result = handler({"include_all_history": args.include_all_history}, None)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
