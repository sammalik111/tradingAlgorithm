import uuid

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from trading_backend.db.base import Base
from trading_backend.models.enums import OrderSide
from trading_backend.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class SimulatedOrder(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A logged paper-trade entry against a recommendation.

    No real brokerage call is ever made here -- see
    integrations/robinhood/client.py for why live order placement isn't
    wired up yet. `price` is whatever the caller previewed/confirmed at,
    not a fetched market quote (this repo has no market-data integration).
    """

    __tablename__ = "simulated_orders"

    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendations.id"), index=True
    )
    ticker: Mapped[str] = mapped_column(String(32))
    side: Mapped[OrderSide] = mapped_column(Enum(OrderSide, name="order_side"))
    quantity: Mapped[float] = mapped_column(Numeric(16, 4))
    price: Mapped[float] = mapped_column(Numeric(16, 2))
    notional_value: Mapped[float] = mapped_column(Numeric(16, 2))
