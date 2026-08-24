import pytest
from pydantic import ValidationError

from trading_backend.schemas.order import SimulatedOrderCreate


def test_simulated_order_create_accepts_a_valid_payload():
    order = SimulatedOrderCreate(side="buy", quantity=5, price=120.50)

    assert order.side == "buy"
    assert order.quantity == 5
    assert order.price == 120.50


@pytest.mark.parametrize("quantity,price", [(0, 10), (-1, 10), (5, 0), (5, -10)])
def test_simulated_order_create_rejects_non_positive_quantity_or_price(quantity, price):
    with pytest.raises(ValidationError):
        SimulatedOrderCreate(side="buy", quantity=quantity, price=price)
