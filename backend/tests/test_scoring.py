from datetime import date, timedelta

from trading_backend.algorithms.scoring import ScorableTrade, score_ticker
from trading_backend.models.enums import RecommendationDirection, TransactionType

TODAY = date(2026, 8, 23)


def _trade(
    politician_id: str, days_ago: int, transaction_type: TransactionType, amount: float
) -> ScorableTrade:
    return ScorableTrade(
        politician_id=politician_id,
        transaction_type=transaction_type,
        transaction_date=TODAY - timedelta(days=days_ago),
        amount_mid=amount,
    )


def test_single_recent_large_buy_scores_bullish():
    trades = [_trade("p1", 1, TransactionType.BUY, 1_000_000)]
    score = score_ticker("NVDA", trades, TODAY)

    assert score.direction == RecommendationDirection.BUY
    assert score.signal_score > 0


def test_stale_trade_contributes_less_than_recent_trade():
    recent = score_ticker("AAPL", [_trade("p1", 1, TransactionType.BUY, 500_000)], TODAY)
    stale = score_ticker("AAPL", [_trade("p1", 180, TransactionType.BUY, 500_000)], TODAY)

    assert recent.signal_score > stale.signal_score


def test_multiple_politicians_agreeing_boosts_score_over_single_trader():
    single = score_ticker("TSLA", [_trade("p1", 1, TransactionType.BUY, 200_000)], TODAY)
    consensus = score_ticker(
        "TSLA",
        [
            _trade("p1", 1, TransactionType.BUY, 200_000),
            _trade("p2", 2, TransactionType.BUY, 200_000),
            _trade("p3", 3, TransactionType.BUY, 200_000),
        ],
        TODAY,
    )

    assert consensus.signal_score > single.signal_score
    assert consensus.agreeing_politicians == 3


def test_opposing_trades_pull_score_toward_hold():
    trades = [
        _trade("p1", 1, TransactionType.BUY, 500_000),
        _trade("p2", 1, TransactionType.SELL, 500_000),
    ]
    score = score_ticker("MSFT", trades, TODAY)

    assert abs(score.signal_score) < 0.15
    assert score.direction == RecommendationDirection.HOLD


def test_no_trades_yields_neutral_hold():
    score = score_ticker("GOOG", [], TODAY)

    assert score.signal_score == 0
    assert score.direction == RecommendationDirection.HOLD
