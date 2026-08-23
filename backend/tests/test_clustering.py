from trading_backend.algorithms.clustering import consensus, consensus_multiplier
from trading_backend.models.enums import TransactionType


def test_consensus_picks_majority_direction():
    result = consensus(
        {
            TransactionType.BUY: {"p1", "p2", "p3"},
            TransactionType.SELL: {"p4"},
        }
    )

    assert result.majority_direction == TransactionType.BUY
    assert result.agreeing_politicians == 3
    assert result.total_politicians == 4


def test_consensus_multiplier_grows_with_more_agreement_but_diminishes():
    m1 = consensus_multiplier(1)
    m2 = consensus_multiplier(2)
    m5 = consensus_multiplier(5)

    assert m1 == 1.0
    assert m2 > m1
    assert m5 > m2
    assert (m5 - m2) < (m2 - m1) * 3


def test_empty_consensus_is_safe():
    result = consensus({})

    assert result.total_politicians == 0
