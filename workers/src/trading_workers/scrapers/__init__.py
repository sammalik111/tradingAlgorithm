from trading_workers.scrapers.base import RawTradeRecord, Scraper
from trading_workers.scrapers.house_stock_watcher import HouseStockWatcherScraper
from trading_workers.scrapers.quiver_quant import QuiverQuantNotConfiguredError, QuiverQuantScraper
from trading_workers.scrapers.senate_efd import SenateEfdScraper
from trading_workers.scrapers.senate_stock_watcher import SenateStockWatcherScraper

# Every source the real nightly job attempts. Sources gated behind an API
# key (currently only Quiver) raise a *NotConfiguredError that the job
# catches and reports as skipped, so a missing optional key never breaks
# the free sources -- see jobs/nightly_scrape.py.
#
# SenateStockWatcherScraper (the GitHub-mirrored dataset, frozen since
# March 2021 -- see its module docstring) is deliberately NOT in this
# list: it would never contribute anything to a normal run since nothing
# in it is within the recency window, and SenateEfdScraper is the live
# replacement. It's still importable directly for a one-off historical
# backfill (see documentation/workers.md).
ALL_SCRAPERS: list[Scraper] = [
    SenateEfdScraper(),
    HouseStockWatcherScraper(),
    QuiverQuantScraper(),
]

__all__ = [
    "ALL_SCRAPERS",
    "HouseStockWatcherScraper",
    "QuiverQuantNotConfiguredError",
    "QuiverQuantScraper",
    "RawTradeRecord",
    "Scraper",
    "SenateEfdScraper",
    "SenateStockWatcherScraper",
]
