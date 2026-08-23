import pytest

from trading_workers.models.enums import TransactionType
from trading_workers.scrapers.transaction_types import parse_transaction_type


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Purchase", TransactionType.BUY),
        ("Sale (Full)", TransactionType.SELL),
        ("Sale (Partial)", TransactionType.SELL),
        ("Exchange", TransactionType.EXCHANGE),
    ],
)
def test_known_types(raw, expected):
    assert parse_transaction_type(raw) == expected


def test_unknown_type_raises():
    with pytest.raises(ValueError):
        parse_transaction_type("Gift")
