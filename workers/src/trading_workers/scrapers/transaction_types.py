from trading_workers.models.enums import TransactionType

_PURCHASE_KEYWORDS = ("purchase", "buy")
_SALE_KEYWORDS = ("sale", "sell")
_EXCHANGE_KEYWORDS = ("exchange",)


def parse_transaction_type(raw: str) -> TransactionType:
    """Map a disclosure's free-text transaction type ("Purchase",
    "Sale (Partial)", "Sale (Full)", "Exchange", ...) to our enum.
    """
    lowered = raw.lower()
    if any(keyword in lowered for keyword in _EXCHANGE_KEYWORDS):
        return TransactionType.EXCHANGE
    if any(keyword in lowered for keyword in _SALE_KEYWORDS):
        return TransactionType.SELL
    if any(keyword in lowered for keyword in _PURCHASE_KEYWORDS):
        return TransactionType.BUY
    raise ValueError(f"Unrecognized transaction type: {raw!r}")
