from dataclasses import dataclass
from typing import Protocol


class RobinhoodNotConfiguredError(RuntimeError):
    """Raised until real Robinhood credentials and an execution policy are
    wired up. Deliberately unimplemented for v1: this repo currently ships
    read-only recommendations, no order placement.
    """


@dataclass(frozen=True)
class RobinhoodPosition:
    ticker: str
    quantity: float
    average_buy_price: float


class RobinhoodClient(Protocol):
    """Interface the recommendation engine will use once account
    integration is enabled, so callers can depend on this shape without
    caring whether it's backed by `robin_stocks` or a future replacement.
    """

    async def get_positions(self) -> list[RobinhoodPosition]: ...


class UnconfiguredRobinhoodClient:
    """Placeholder implementation. Every method raises until real
    credentials (via AWS Secrets Manager) and an explicit decision on
    order-placement scope are provided.
    """

    async def get_positions(self) -> list[RobinhoodPosition]:
        raise RobinhoodNotConfiguredError(
            "Robinhood integration is not yet configured. See "
            "documentation/backend.md for the planned credential flow."
        )


def get_robinhood_client() -> RobinhoodClient:
    return UnconfiguredRobinhoodClient()
