"""Tests for the real BinanceExchange connector"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import ccxt.async_support as ccxt_async

from src.exchanges.binance_exchange import BinanceExchange


@pytest.fixture
def config_sandbox():
    return {
        "sandbox": True,
        "api_key": "test_key",
        "api_secret": "test_secret",
    }


@pytest.fixture
def config_no_keys():
    return {
        "sandbox": True,
        "api_key": "",
        "api_secret": "",
    }


@pytest.fixture
def exchange(config_sandbox):
    return BinanceExchange(config_sandbox)


@pytest.fixture
def exchange_no_keys(config_no_keys):
    return BinanceExchange(config_no_keys)


# -- constructor --


def test_authenticated_with_keys(config_sandbox):
    ex = BinanceExchange(config_sandbox)
    assert ex._authenticated is True


def test_not_authenticated_without_keys(config_no_keys):
    ex = BinanceExchange(config_no_keys)
    assert ex._authenticated is False


def test_sandbox_flag(config_sandbox):
    ex = BinanceExchange(config_sandbox)
    assert ex.sandbox is True


# -- initialize --


@pytest.mark.asyncio
async def test_initialize_creates_client_and_loads_markets(exchange):
    with patch("src.exchanges.binance_exchange.ccxt_async") as mock_ccxt:
        mock_client = AsyncMock()
        mock_client.set_sandbox_mode = MagicMock()  # sync method on real client
        mock_ccxt.binance.return_value = mock_client

        await exchange.initialize()

        mock_ccxt.binance.assert_called_once()
        mock_client.set_sandbox_mode.assert_called_once_with(True)
        mock_client.load_markets.assert_awaited_once()


@pytest.mark.asyncio
async def test_initialize_no_sandbox_when_live():
    ex = BinanceExchange({"sandbox": False, "api_key": "k", "api_secret": "s"})
    with patch("src.exchanges.binance_exchange.ccxt_async") as mock_ccxt:
        mock_client = AsyncMock()
        mock_ccxt.binance.return_value = mock_client

        await ex.initialize()

        mock_client.set_sandbox_mode.assert_not_called()


# -- get_ohlcv --


@pytest.mark.asyncio
async def test_get_ohlcv_returns_data(exchange):
    fake_candles = [[1700000000000, 50000, 50100, 49900, 50050, 1234.5]]
    exchange.client = AsyncMock()
    exchange.client.fetch_ohlcv = AsyncMock(return_value=fake_candles)

    result = await exchange.get_ohlcv("BTC/USDT", "5m", limit=1)

    assert result == fake_candles
    exchange.client.fetch_ohlcv.assert_awaited_once_with("BTC/USDT", "5m", limit=1)


@pytest.mark.asyncio
async def test_get_ohlcv_network_error_returns_empty(exchange):
    exchange.client = AsyncMock()
    exchange.client.fetch_ohlcv = AsyncMock(
        side_effect=ccxt_async.NetworkError("timeout")
    )

    result = await exchange.get_ohlcv("BTC/USDT", "5m")

    assert result == []


@pytest.mark.asyncio
async def test_get_ohlcv_exchange_error_returns_empty(exchange):
    exchange.client = AsyncMock()
    exchange.client.fetch_ohlcv = AsyncMock(
        side_effect=ccxt_async.ExchangeError("bad symbol")
    )

    result = await exchange.get_ohlcv("FAKE/USDT", "5m")

    assert result == []


# -- get_ticker --


@pytest.mark.asyncio
async def test_get_ticker_returns_float(exchange):
    exchange.client = AsyncMock()
    exchange.client.fetch_ticker = AsyncMock(return_value={"last": 51234.56})

    result = await exchange.get_ticker("BTC/USDT")

    assert result == 51234.56
    assert isinstance(result, float)


@pytest.mark.asyncio
async def test_get_ticker_error_returns_zero(exchange):
    exchange.client = AsyncMock()
    exchange.client.fetch_ticker = AsyncMock(
        side_effect=ccxt_async.NetworkError("down")
    )

    result = await exchange.get_ticker("BTC/USDT")

    assert result == 0.0


# -- orders --


@pytest.mark.asyncio
async def test_buy_order_normalizes_response(exchange):
    exchange.client = AsyncMock()
    exchange.client.create_market_buy_order = AsyncMock(
        return_value={
            "id": "12345",
            "symbol": "BTC/USDT",
            "side": "buy",
            "amount": 0.001,
            "average": 50500.0,
            "price": None,
            "filled": 0.001,
            "status": "closed",
            "extra_field": "ignored",
        }
    )

    result = await exchange.create_market_buy_order("BTC/USDT", 0.001)

    assert result == {
        "id": "12345",
        "symbol": "BTC/USDT",
        "side": "buy",
        "amount": 0.001,
        "price": 50500.0,
        "filled": 0.001,
        "status": "closed",
    }


@pytest.mark.asyncio
async def test_sell_order_insufficient_funds_returns_empty(exchange):
    exchange.client = AsyncMock()
    exchange.client.create_market_sell_order = AsyncMock(
        side_effect=ccxt_async.InsufficientFunds("no funds")
    )

    result = await exchange.create_market_sell_order("BTC/USDT", 100.0)

    assert result == {}


@pytest.mark.asyncio
async def test_order_without_auth_raises(exchange_no_keys):
    with pytest.raises(ccxt_async.AuthenticationError):
        await exchange_no_keys.create_market_buy_order("BTC/USDT", 0.001)


# -- get_positions --


@pytest.mark.asyncio
async def test_get_positions_maps_balances(exchange):
    exchange.client = AsyncMock()
    exchange.client.fetch_balance = AsyncMock(
        return_value={"total": {"BTC": 0.5, "ETH": 2.0, "USDT": 1000.0}}
    )
    exchange.client.markets = {
        "BTC/USDT": {"base": "BTC", "quote": "USDT", "spot": True},
        "ETH/USDT": {"base": "ETH", "quote": "USDT", "spot": True},
    }
    exchange.client.fetch_ticker = AsyncMock(
        side_effect=lambda s: {"last": 50000.0} if "BTC" in s else {"last": 3000.0}
    )

    result = await exchange.get_positions()

    assert "BTC/USDT" in result
    assert result["BTC/USDT"]["quantity"] == 0.5
    assert result["BTC/USDT"]["side"] == "long"
    assert "ETH/USDT" in result
    assert result["ETH/USDT"]["quantity"] == 2.0
    # USDT itself should not appear
    assert "USDT/USDT" not in result


@pytest.mark.asyncio
async def test_get_positions_skips_zero_balances(exchange):
    exchange.client = AsyncMock()
    exchange.client.fetch_balance = AsyncMock(
        return_value={"total": {"BTC": 0.0, "ETH": 0.0, "USDT": 500.0}}
    )
    exchange.client.markets = {
        "BTC/USDT": {"base": "BTC", "quote": "USDT", "spot": True},
    }

    result = await exchange.get_positions()

    assert result == {}


@pytest.mark.asyncio
async def test_get_positions_without_auth_raises(exchange_no_keys):
    with pytest.raises(ccxt_async.AuthenticationError):
        await exchange_no_keys.get_positions()


# -- normalize_order --


def test_normalize_order_uses_average_over_price():
    result = BinanceExchange._normalize_order(
        {"id": "1", "symbol": "X/Y", "side": "buy", "amount": 1, "average": 100.0, "price": None, "filled": 1, "status": "closed"}
    )
    assert result["price"] == 100.0


def test_normalize_order_falls_back_to_price():
    result = BinanceExchange._normalize_order(
        {"id": "1", "symbol": "X/Y", "side": "buy", "amount": 1, "average": None, "price": 99.0, "filled": 1, "status": "closed"}
    )
    assert result["price"] == 99.0


# -- close --


@pytest.mark.asyncio
async def test_close_closes_client(exchange):
    exchange.client = AsyncMock()

    await exchange.close()

    exchange.client.close.assert_awaited_once()
