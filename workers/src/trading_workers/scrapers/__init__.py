from trading_workers.scrapers.base import RawTradeRecord, Scraper
from trading_workers.scrapers.house_stock_watcher import HouseStockWatcherScraper
from trading_workers.scrapers.quiver_quant import QuiverQuantNotConfiguredError, QuiverQuantScraper
from trading_workers.scrapers.senate_stock_watcher import SenateStockWatcherScraper

# Every source the nightly job attempts. Sources gated behind an API key
# (currently only Quiver) raise a *NotConfiguredError that the job catches
# and logs, so a missing optional key never breaks the free sources.
ALL_SCRAPERS: list[Scraper] = [
    SenateStockWatcherScraper(),
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
    "SenateStockWatcherScraper",
]
