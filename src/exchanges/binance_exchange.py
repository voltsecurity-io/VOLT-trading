"""
VOLT Trading - Real Binance Exchange Connector
Uses ccxt async library for live Binance spot trading
"""

import ccxt.async_support as ccxt_async
from typing import Dict, Any, Optional

from src.exchanges.exchange_factory import BaseExchange
from src.utils.logger import get_logger


class BinanceExchange(BaseExchange):
    """Real Binance exchange implementation via ccxt"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key", "")
        self.api_secret = config.get("api_secret", "")
        self.client: Optional[ccxt_async.binance] = None
        self._authenticated = bool(self.api_key and self.api_secret)

    async def initialize(self):
        """Initialize Binance connection via ccxt"""
        self.logger.info("Initializing Binance exchange...")

        self.client = ccxt_async.binance(
            {
                "apiKey": self.api_key if self.api_key else None,
                "secret": self.api_secret if self.api_secret else None,
                "enableRateLimit": True,
                "options": {
                    "defaultType": "spot",
                },
            }
        )

        if self.sandbox:
            self.client.set_sandbox_mode(True)
            self.logger.info("Sandbox mode enabled (Binance testnet)")

        await self.client.load_markets()

        mode = "sandbox" if self.sandbox else "LIVE"
        auth = "authenticated" if self._authenticated else "public-only (no API keys)"
        self.logger.info(f"Binance exchange ready — {mode}, {auth}")

    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> list:
        """Fetch OHLCV candles from Binance"""
        try:
            # ccxt returns [[timestamp_ms, open, high, low, close, volume], ...]
            return await self.client.fetch_ohlcv(symbol, timeframe, limit=limit)
        except ccxt_async.NetworkError as e:
            self.logger.error(f"Network error fetching OHLCV for {symbol}: {e}")
            return []
        except ccxt_async.ExchangeError as e:
            self.logger.error(f"Exchange error fetching OHLCV for {symbol}: {e}")
            return []

    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Fetch last traded price from Binance"""
        try:
            ticker = await self.client.fetch_ticker(symbol)

            def safe_float(val, default=0.0):
                if val is None:
                    return default
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return default

            return {
                "last": safe_float(ticker.get("last")),
                "bid": safe_float(ticker.get("bid")),
                "ask": safe_float(ticker.get("ask")),
                "volume": safe_float(ticker.get("volume")),
                "percentage": safe_float(ticker.get("percentage")),
            }
        except ccxt_async.NetworkError as e:
            self.logger.error(f"Network error fetching ticker for {symbol}: {e}")
            return {"last": 0, "bid": 0, "ask": 0, "volume": 0, "percentage": 0}
        except ccxt_async.ExchangeError as e:
            self.logger.error(f"Exchange error fetching ticker for {symbol}: {e}")
            return {"last": 0, "bid": 0, "ask": 0, "volume": 0, "percentage": 0}

    async def create_market_buy_order(
        self, symbol: str, amount: float
    ) -> Dict[str, Any]:
        """Place a market buy order on Binance"""
        self._require_auth("create_market_buy_order")
        try:
            order = await self.client.create_market_buy_order(symbol, amount)
            return self._normalize_order(order)
        except ccxt_async.InsufficientFunds as e:
            self.logger.error(f"Insufficient funds for buy {symbol}: {e}")
            return {}
        except ccxt_async.InvalidOrder as e:
            self.logger.error(f"Invalid buy order for {symbol}: {e}")
            return {}
        except ccxt_async.NetworkError as e:
            self.logger.error(f"Network error placing buy for {symbol}: {e}")
            return {}
        except ccxt_async.ExchangeError as e:
            self.logger.error(f"Exchange error placing buy for {symbol}: {e}")
            return {}

    async def create_market_sell_order(
        self, symbol: str, amount: float
    ) -> Dict[str, Any]:
        """Place a market sell order on Binance"""
        self._require_auth("create_market_sell_order")
        try:
            order = await self.client.create_market_sell_order(symbol, amount)
            return self._normalize_order(order)
        except ccxt_async.InsufficientFunds as e:
            self.logger.error(f"Insufficient funds for sell {symbol}: {e}")
            return {}
        except ccxt_async.InvalidOrder as e:
            self.logger.error(f"Invalid sell order for {symbol}: {e}")
            return {}
        except ccxt_async.NetworkError as e:
            self.logger.error(f"Network error placing sell for {symbol}: {e}")
            return {}
        except ccxt_async.ExchangeError as e:
            self.logger.error(f"Exchange error placing sell for {symbol}: {e}")
            return {}

    async def get_positions(self) -> Dict[str, Any]:
        """Map Binance spot balances to position dicts.

        Binance spot has balances, not positions. We convert non-zero
        balances for configured trading pairs into the position format
        that TradingEngine expects.
        """
        self._require_auth("get_positions")
        try:
            balance = await self.client.fetch_balance()
            positions = {}

            # Find which base currencies have USDT spot markets
            tradeable_bases = {
                m["base"]
                for m in self.client.markets.values()
                if m.get("quote") == "USDT" and m.get("spot")
            }

            for currency, total in balance.get("total", {}).items():
                total = float(total) if total else 0.0
                if total <= 0 or currency == "USDT":
                    continue
                if currency not in tradeable_bases:
                    continue

                symbol = f"{currency}/USDT"
                current_price = await self.get_ticker(symbol)

                positions[symbol] = {
                    "symbol": symbol,
                    "quantity": total,
                    "entry_price": current_price,
                    "unrealized_pnl": 0.0,
                    "side": "long",
                }

            return positions

        except ccxt_async.AuthenticationError as e:
            self.logger.error(f"Auth error fetching positions: {e}")
            return {}
        except ccxt_async.NetworkError as e:
            self.logger.error(f"Network error fetching positions: {e}")
            return {}
        except ccxt_async.ExchangeError as e:
            self.logger.error(f"Exchange error fetching positions: {e}")
            return {}

    async def get_balance(self) -> Dict[str, Any]:
        """Fetch account balance from Binance"""
        self._require_auth("get_balance")
        try:
            balance = await self.client.fetch_balance()
            return balance.get("total", {})
        except ccxt_async.AuthenticationError as e:
            self.logger.error(f"Auth error fetching balance: {e}")
            return {}
        except ccxt_async.NetworkError as e:
            self.logger.error(f"Network error fetching balance: {e}")
            return {}
        except ccxt_async.ExchangeError as e:
            self.logger.error(f"Exchange error fetching balance: {e}")
            return {}

    async def close(self):
        """Close the ccxt client and release aiohttp session"""
        if self.client:
            await self.client.close()
            self.logger.info("Binance exchange connection closed")

    # -- helpers --

    def _require_auth(self, method_name: str):
        """Raise if API keys are not configured"""
        if not self._authenticated:
            raise ccxt_async.AuthenticationError(
                f"{method_name} requires API keys. "
                f"Set exchange.api_key and exchange.api_secret in config."
            )

    @staticmethod
    def _normalize_order(order: dict) -> Dict[str, Any]:
        """Convert ccxt unified order to the format TradingEngine expects"""
        return {
            "id": order.get("id", ""),
            "symbol": order.get("symbol", ""),
            "side": order.get("side", ""),
            "amount": float(order.get("amount", 0) or 0),
            "price": float(order.get("average", 0) or order.get("price", 0) or 0),
            "filled": float(order.get("filled", 0) or 0),
            "status": order.get("status", ""),
        }
