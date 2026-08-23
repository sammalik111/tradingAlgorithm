from datetime import date

from pydantic import BaseModel

from trading_workers.models.enums import Chamber, SourceCode, TransactionType
from trading_workers.scrapers.base import RawTradeRecord


class TradeIngestMessage(BaseModel):
    """Wire format for one scraped trade on the SQS ingest queue. A 1:1
    serialization of `RawTradeRecord`, kept separate so the SQS contract
    doesn't silently change if the scraper-internal dataclass does.
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

    @classmethod
    def from_record(cls, record: RawTradeRecord) -> "TradeIngestMessage":
        return cls(**record.__dict__)

    def to_record(self) -> RawTradeRecord:
        return RawTradeRecord(**self.model_dump())
