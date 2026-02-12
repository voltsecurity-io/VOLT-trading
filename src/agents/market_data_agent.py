"""
Market Data Agent
Handles real-time market data collection and processing
"""

import asyncio
import random
from typing import Dict, List, Any
from datetime import datetime

from src.core.config_manager import ConfigManager
from src.utils.logger import get_logger


class MarketDataAgent:
    """Agent responsible for market data collection"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        self.config = config_manager.get_trading_config()

        self.running = False
        self.market_data = {}
        self.last_update = None

    async def initialize(self):
        """Initialize market data agent"""
        self.logger.info("📊 Initializing Market Data Agent...")

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
        for symbol in self.symbols:
            try:
                # Simulated market data - in production, use real exchange APIs
                data = await self._fetch_symbol_data(symbol)

                if data:
                    self.market_data[symbol] = data

            except Exception as e:
                self.logger.error(f"❌ Error fetching data for {symbol}: {e}")

        self.last_update = datetime.now()

    async def _fetch_symbol_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch data for a specific symbol"""
        # Simulated data - replace with real API calls
        base_price = self._get_base_price(symbol)

        # Generate realistic price movements
        price = base_price + random.uniform(-0.02, 0.02) * base_price
        volume = random.uniform(1000, 10000)

        return {
            "symbol": symbol,
            "price": price,
            "volume": volume,
            "change_24h": random.uniform(-5, 5),
            "high_24h": price * 1.02,
            "low_24h": price * 0.98,
            "timestamp": datetime.now().isoformat(),
            "bid": price * 0.999,
            "ask": price * 1.001,
            "spread": price * 0.002,
            "liquidity_score": random.uniform(0.7, 1.0),
        }

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
        if data["price"] <= 0 or data["volume"] <= 0:
            return False

        # Check timestamp is recent
        try:
            timestamp = datetime.fromisoformat(data["timestamp"])
            age = (datetime.now() - timestamp).total_seconds()
            if age > 300:  # 5 minutes
                return False
        except:
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

    def _get_base_price(self, symbol: str) -> float:
        """Get base price for symbol"""
        prices = {
            "BTC/USDT": 50000.0,
            "ETH/USDT": 3000.0,
            "BNB/USDT": 400.0,
            "SOL/USDT": 150.0,
            "AVAX/USDT": 40.0,
            "MATIC/USDT": 0.9,
        }
        return prices.get(symbol, 100.0)

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
