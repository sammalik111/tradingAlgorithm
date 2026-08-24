import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from trading_backend.models.enums import OrderSide


class SimulatedOrderCreate(BaseModel):
    """User-entered order preview -- `price` is whatever the caller is
    previewing/confirming at, not a fetched market quote. No brokerage
    integration exists yet; see integrations/robinhood/client.py.
    """

    side: OrderSide
    quantity: float = Field(gt=0)
    price: float = Field(gt=0)


class SimulatedOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    recommendation_id: uuid.UUID
    ticker: str
    side: OrderSide
    quantity: float
    price: float
    notional_value: float
    created_at: datetime
