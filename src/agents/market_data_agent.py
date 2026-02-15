"""
Market Data Agent
Handles real-time market data collection and processing
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

from src.core.config_manager import ConfigManager
from src.utils.logger import get_logger
from src.exchanges.exchange_factory import BaseExchange


class MarketDataAgent:
    """Agent responsible for market data collection"""

    def __init__(
        self, config_manager: ConfigManager, exchange: Optional[BaseExchange] = None
    ):
        self.config_manager = config_manager
        self.exchange = exchange
        self.logger = get_logger(__name__)
        self.config = config_manager.get_trading_config()

        self.running = False
        self.market_data = {}
        self.last_update = None

    async def initialize(self):
        """Initialize market data agent"""
        self.logger.info("📊 Initializing Market Data Agent...")

        if not self.exchange:
            self.logger.warning(
                "⚠️ No exchange provided - MarketDataAgent will not function properly"
            )

        # Setup data sources
        self.symbols = self.config.get(
            "pairs", ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"]
        )

        self.timeframe = self.config.get("timeframe", "5m")

        self.logger.info(
            f"📈 Tracking {len(self.symbols)} symbols on {self.timeframe} timeframe"
        )

    async def start(self):
        """Start market data collection"""
        if self.running:
            return

        self.running = True
        self.logger.info("🚀 Starting Market Data Agent...")

        while self.running:
            try:
                # Collect market data
                await self._collect_market_data()

                # Process and validate data
                await self._process_data()

                # Sleep until next update
                await asyncio.sleep(self._get_update_interval())

            except Exception as e:
                self.logger.error(f"❌ Error in market data collection: {e}")
                await asyncio.sleep(5)  # Brief pause on error

    async def stop(self):
        """Stop market data collection"""
        self.running = False
        self.logger.info("🛑 Market Data Agent stopped")

    async def get_latest_data(self) -> Dict[str, Any]:
        """Get latest market data"""
        return {
            "symbols": list(self.market_data.keys()),
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "quality": self._assess_data_quality(),
            "data_summary": self._generate_data_summary(),
        }

    async def _collect_market_data(self):
        """Collect market data from exchanges"""
        if not self.exchange:
            self.logger.error("❌ No exchange available for data collection")
            return

        for symbol in self.symbols:
            try:
                # Fetch real market data from exchange
                data = await self._fetch_symbol_data(symbol)

                if data:
                    self.market_data[symbol] = data

            except Exception as e:
                self.logger.error(f"❌ Error fetching data for {symbol}: {e}")

        self.last_update = datetime.now()

    async def _fetch_symbol_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch data for a specific symbol from exchange"""
        if not self.exchange:
            return {}

        try:
            # Get current ticker price (now returns dict)
            ticker = await self.exchange.get_ticker(symbol)

            # Handle both dict and float returns for backwards compatibility
            if isinstance(ticker, dict):
                last_val = ticker.get("last")
                bid_val = ticker.get("bid")
                price = (
                    float(last_val)
                    if last_val is not None
                    else (float(bid_val) if bid_val is not None else 0)
                )
            else:
                price = float(ticker) if ticker else 0

            # Skip if price is invalid
            if price <= 0:
                self.logger.warning(f"⚠️ Invalid price for {symbol}")
                return {}

            # Get OHLCV data for volume and price stats
            ohlcv = await self.exchange.get_ohlcv(symbol, self.timeframe, limit=24)

            if not ohlcv or price <= 0:
                self.logger.warning(f"⚠️ No data available for {symbol}")
                return {}

            # Convert OHLCV to DataFrame for easier analysis
            try:
                df = pd.DataFrame(
                    ohlcv,
                    columns=["timestamp", "open", "high", "low", "close", "volume"],
                )
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to create DataFrame for {symbol}: {e}")
                return {}

            # Calculate 24h stats
            high_24h = df["high"].max()
            low_24h = df["low"].min()
            first_price = df.iloc[0]["close"]
            change_24h = ((price - first_price) / first_price) * 100

            # Calculate current volume
            current_volume = df["volume"].sum()

            # Calculate spread approximation (0.1% typical for major pairs)
            spread = price * 0.001

            return {
                "symbol": symbol,
                "price": price,
                "volume": current_volume,
                "change_24h": change_24h,
                "high_24h": high_24h,
                "low_24h": low_24h,
                "timestamp": datetime.now().isoformat(),
                "bid": price - spread / 2,
                "ask": price + spread / 2,
                "spread": spread,
                "liquidity_score": min(current_volume / 1000000, 1.0),  # Normalized
                "data_points": len(df),
            }

        except Exception as e:
            self.logger.error(f"❌ Error fetching symbol data for {symbol}: {e}")
            return {}

    async def _process_data(self):
        """Process and validate collected data"""
        for symbol, data in self.market_data.items():
            # Validate data quality
            if self._validate_symbol_data(data):
                # Apply any necessary transformations
                data["processed"] = True
                data["confidence"] = self._calculate_confidence(data)
            else:
                self.logger.warning(f"⚠️ Invalid data for {symbol}")
                data["valid"] = False

    def _validate_symbol_data(self, data: Dict[str, Any]) -> bool:
        """Validate market data"""
        if not data:
            return False

        # Check required fields
        required_fields = ["price", "volume", "timestamp"]
        if not all(field in data for field in required_fields):
            return False

        # Check data ranges
        if data["price"] <= 0 or data["volume"] < 0:
            return False

        # Check timestamp is recent (within 5 minutes, or just valid format)
        try:
            timestamp = datetime.fromisoformat(data["timestamp"])
            # Allow any timestamp for now - don't enforce freshness in validation
            # Freshness is tracked separately in data quality metrics
        except (ValueError, TypeError):
            return False

        return True

    def _calculate_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate confidence score for data"""
        confidence = 0.5  # Base confidence

        # Volume-based confidence
        if data["volume"] > 5000:
            confidence += 0.2

        # Liquidity-based confidence
        liquidity = data.get("liquidity_score", 0.5)
        confidence += liquidity * 0.3

        return min(confidence, 1.0)

    def _assess_data_quality(self) -> float:
        """Assess overall data quality"""
        if not self.market_data:
            return 0.0

        total_confidence = 0.0
        valid_symbols = 0

        for symbol, data in self.market_data.items():
            if data.get("valid", True):
                total_confidence += data.get("confidence", 0.5)
                valid_symbols += 1

        return total_confidence / valid_symbols if valid_symbols > 0 else 0.0

    def _generate_data_summary(self) -> Dict[str, Any]:
        """Generate summary of market data"""
        if not self.market_data:
            return {}

        total_volume = sum(data.get("volume", 0) for data in self.market_data.values())
        avg_confidence = self._assess_data_quality()

        return {
            "total_symbols": len(self.market_data),
            "total_volume": total_volume,
            "average_confidence": avg_confidence,
            "data_freshness": "fresh"
            if self.last_update and (datetime.now() - self.last_update).seconds < 60
            else "stale",
        }

    def _get_update_interval(self) -> int:
        """Get data update interval based on timeframe"""
        timeframe = self.config.get("timeframe", "5m")

        if timeframe.endswith("m"):
            minutes = int(timeframe[:-1])
            return max(minutes * 60, 30)  # Minimum 30 seconds
        elif timeframe.endswith("h"):
            hours = int(timeframe[:-1])
            return max(hours * 3600, 300)  # Minimum 5 minutes
        else:
            return 300  # Default 5 minutes

    async def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "running": self.running,
            "symbols_tracked": len(self.symbols),
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "data_quality": self._assess_data_quality(),
            "status": "active" if self.running else "stopped",
        }
