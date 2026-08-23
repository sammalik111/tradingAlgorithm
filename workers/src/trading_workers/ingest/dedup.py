import hashlib
import uuid
from datetime import date

from trading_workers.models.enums import TransactionType


def compute_dedup_key(
    politician_id: uuid.UUID,
    ticker: str,
    transaction_date: date,
    transaction_type: TransactionType,
    amount_min: float,
    amount_max: float,
) -> str:
    """Deterministic key identifying "the same disclosed trade" regardless
    of which source reported it. Two `RawTradeEvent`s from different
    sources that produce the same key collapse into one `CanonicalTrade`.
    """
    payload = "|".join(
        [
            str(politician_id),
            ticker,
            transaction_date.isoformat(),
            transaction_type.value,
            f"{amount_min:.2f}",
            f"{amount_max:.2f}",
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
