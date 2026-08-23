import uuid
from datetime import date

from trading_workers.ingest.dedup import compute_dedup_key
from trading_workers.models.enums import TransactionType

POLITICIAN_ID = uuid.uuid4()


def _key(**overrides):
    defaults = dict(
        politician_id=POLITICIAN_ID,
        ticker="AAPL",
        transaction_date=date(2026, 8, 1),
        transaction_type=TransactionType.BUY,
        amount_min=1001.0,
        amount_max=15000.0,
    )
    return compute_dedup_key(**{**defaults, **overrides})


def test_identical_trades_produce_identical_keys():
    assert _key() == _key()


def test_different_ticker_changes_key():
    assert _key() != _key(ticker="MSFT")


def test_different_amount_bucket_changes_key():
    assert _key() != _key(amount_min=15001.0, amount_max=50000.0)


def test_different_politician_changes_key():
    assert _key() != _key(politician_id=uuid.uuid4())
