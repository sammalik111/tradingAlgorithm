import pytest

from trading_backend.integrations.robinhood.client import (
    RobinhoodNotConfiguredError,
    get_robinhood_client,
)


async def test_unconfigured_client_raises_on_use():
    client = get_robinhood_client()

    with pytest.raises(RobinhoodNotConfiguredError):
        await client.get_positions()
