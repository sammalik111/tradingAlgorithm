from dataclasses import dataclass
from datetime import date
from typing import Protocol

from trading_workers.models.enums import Chamber, SourceCode, TransactionType


@dataclass(frozen=True)
class RawTradeRecord:
    """One disclosure record exactly as a scraper parsed it, before politician
    resolution or deduplication happen in `ingest/`.
    """

    politician_full_name: str
    chamber: Chamber
    ticker: str
    asset_name: str
    transaction_type: TransactionType
    transaction_date: date
    disclosure_date: date
    amount_min: float
    amount_max: float
    source_code: SourceCode
    external_id: str | None
    raw_payload: dict


class Scraper(Protocol):
    source_code: SourceCode

    async def fetch(self) -> list[RawTradeRecord]: ...
