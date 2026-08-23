import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from trading_backend.models.enums import TransactionType


class CanonicalTradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    politician_id: uuid.UUID
    ticker: str
    asset_name: str
    transaction_type: TransactionType
    transaction_date: date
    disclosure_date: date
    amount_min: float
    amount_max: float
    amount_mid: float
    source_count: int
    first_seen_at: datetime
    last_seen_at: datetime
