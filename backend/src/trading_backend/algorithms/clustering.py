import math
from collections import Counter
from dataclasses import dataclass

from trading_backend.models.enums import TransactionType

CONSENSUS_WEIGHT = 0.35


@dataclass(frozen=True)
class ConsensusResult:
    majority_direction: TransactionType
    agreeing_politicians: int
    total_politicians: int


def consensus(
    politician_id_by_direction: dict[TransactionType, set],
) -> ConsensusResult:
    """Determine whether tracked politicians are trading a ticker in the
    same direction, and by how many distinct people.

    `politician_id_by_direction` maps each transaction type to the set of
    distinct politician ids who traded that direction in the scoring
    window. Ties resolve to whichever direction has the larger set.
    """
    counts = Counter({direction: len(ids) for direction, ids in politician_id_by_direction.items()})
    if not counts:
        return ConsensusResult(TransactionType.BUY, 0, 0)

    majority_direction, agreeing = counts.most_common(1)[0]
    total = sum(counts.values())
    return ConsensusResult(majority_direction, agreeing, total)


def consensus_multiplier(agreeing_politicians: int) -> float:
    """Scale a raw score up when multiple distinct politicians agree on a
    direction. A single trader contributes no multiplier; each additional
    agreeing politician adds a diminishing boost via log1p.
    """
    if agreeing_politicians <= 1:
        return 1.0
    return 1.0 + math.log1p(agreeing_politicians - 1) * CONSENSUS_WEIGHT
