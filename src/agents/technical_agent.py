"""
Technical Analysis Agent
Handles technical indicator calculations and analysis
"""

import asyncio
import random
from typing import Dict, List, Any
from datetime import datetime

from src.core.config_manager import ConfigManager
from src.utils.logger import get_logger


class TechnicalAnalysisAgent:
    """Agent responsible for technical analysis"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = get_logger(__name__)

        self.running = False
        self.technical_signals = {}
        self.indicators = {}

    async def initialize(self):
        """Initialize technical analysis agent"""
        self.logger.info("📈 Initializing Technical Analysis Agent...")

        # Setup technical indicators
        self.indicators = {
            "rsi": {"period": 14, "overbought": 70, "oversold": 30},
            "macd": {"fast": 12, "slow": 26, "signal": 9},
            "bollinger": {"period": 20, "std": 2},
            "sma": {"periods": [20, 50, 200]},
            "ema": {"periods": [12, 26]},
            "volume": {"sma": 20},
        }

        self.logger.info("📊 Technical indicators configured")

    async def start(self):
        """Start technical analysis"""
        if self.running:
            return

        self.running = True
        self.logger.info("🚀 Starting Technical Analysis Agent...")

        while self.running:
            try:
                # Perform technical analysis
                await self._analyze_markets()

                # Generate signals
                await self._generate_signals()

                # Sleep until next analysis
                await asyncio.sleep(60)  # Analyze every minute

            except Exception as e:
                self.logger.error(f"❌ Error in technical analysis: {e}")
                await asyncio.sleep(10)  # Brief pause on error

    async def stop(self):
        """Stop technical analysis"""
        self.running = False
        self.logger.info("🛑 Technical Analysis Agent stopped")

    async def get_signals(self) -> Dict[str, Any]:
        """Get latest technical signals"""
        return {
            "signals": self.technical_signals,
            "signal_count": len(self.technical_signals),
            "confidence": self._calculate_overall_confidence(),
            "last_update": datetime.now().isoformat(),
        }

    async def _analyze_markets(self):
        """Perform technical analysis on all symbols"""
        # Get symbols from config
        symbols = self.config_manager.get(
            "trading.pairs", ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"]
        )

        for symbol in symbols:
            try:
                # Generate simulated price data - in production, use real data
                price_data = self._generate_sample_data(symbol)

                # Calculate indicators
                analysis = self._calculate_indicators(price_data)

                # Store analysis results
                self.technical_signals[symbol] = analysis

            except Exception as e:
                self.logger.error(f"❌ Error analyzing {symbol}: {e}")

    async def _generate_signals(self):
        """Generate trading signals from technical analysis"""
        for symbol, analysis in self.technical_signals.items():
            try:
                # Generate buy/sell signals based on indicators
                signal = self._evaluate_symbol_signals(symbol, analysis)

                # Store signal
                analysis["signal"] = signal
                analysis["signal_timestamp"] = datetime.now().isoformat()

            except Exception as e:
                self.logger.error(f"❌ Error generating signal for {symbol}: {e}")

    def _generate_sample_data(self, symbol: str, periods: int = 100) -> List[float]:
        """Generate sample price data for testing"""
        base_price = self._get_base_price(symbol)
        prices = []
        current_price = base_price

        for _ in range(periods):
            # Random walk with trend
            change = random.uniform(-0.02, 0.02)
            current_price *= 1 + change
            prices.append(current_price)

        return prices

    def _calculate_indicators(self, prices: List[float]) -> Dict[str, Any]:
        """Calculate technical indicators"""
        if len(prices) < 50:
            return {}

        indicators = {}

        # RSI
        indicators["rsi"] = self._calculate_rsi(
            prices, self.indicators["rsi"]["period"]
        )

        # MACD
        macd_data = self._calculate_macd(prices)
        indicators.update(macd_data)

        # Bollinger Bands
        bb_data = self._calculate_bollinger_bands(prices)
        indicators.update(bb_data)

        # Moving Averages
        sma_data = self._calculate_sma(prices, self.indicators["sma"]["periods"])
        indicators.update(sma_data)

        # EMA
        ema_data = self._calculate_ema(prices, self.indicators["ema"]["periods"])
        indicators.update(ema_data)

        # Price action
        current_price = prices[-1]
        indicators["current_price"] = current_price
        indicators["price_change_1"] = (
            (current_price - prices[-2]) / prices[-2] if len(prices) > 1 else 0
        )
        indicators["price_change_5"] = (
            (current_price - prices[-6]) / prices[-6] if len(prices) > 5 else 0
        )

        return indicators

    def _calculate_rsi(self, prices: List[float], period: int) -> float:
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return 50.0

        gains = []
        losses = []

        for i in range(1, len(prices)):
            change = prices[i] - prices[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        if len(gains) < period:
            return 50.0

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _calculate_macd(self, prices: List[float]) -> Dict[str, float]:
        """Calculate MACD indicator"""
        fast = self.indicators["macd"]["fast"]
        slow = self.indicators["macd"]["slow"]
        signal_period = self.indicators["macd"]["signal"]

        if len(prices) < slow:
            return {"macd": 0, "macd_signal": 0, "macd_histogram": 0}

        # Calculate EMAs
        ema_fast = self._calculate_ema_single(prices, fast)
        ema_slow = self._calculate_ema_single(prices, slow)

        macd_line = ema_fast - ema_slow

        # For signal line, we'd need historical MACD values - simplified here
        macd_signal = macd_line * 0.9  # Simplified
        macd_histogram = macd_line - macd_signal

        return {
            "macd": macd_line,
            "macd_signal": macd_signal,
            "macd_histogram": macd_histogram,
        }

    def _calculate_bollinger_bands(self, prices: List[float]) -> Dict[str, float]:
        """Calculate Bollinger Bands"""
        period = self.indicators["bollinger"]["period"]
        std_dev = self.indicators["bollinger"]["std"]

        if len(prices) < period:
            return {"bb_upper": 0, "bb_middle": 0, "bb_lower": 0}

        recent_prices = prices[-period:]
        middle = sum(recent_prices) / period

        variance = sum((price - middle) ** 2 for price in recent_prices) / period
        std = variance**0.5

        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        return {"bb_upper": upper, "bb_middle": middle, "bb_lower": lower}

    def _calculate_sma(
        self, prices: List[float], periods: List[int]
    ) -> Dict[str, float]:
        """Calculate Simple Moving Averages"""
        sma_values = {}

        for period in periods:
            if len(prices) >= period:
                recent_prices = prices[-period:]
                sma = sum(recent_prices) / period
                sma_values[f"sma_{period}"] = sma
            else:
                sma_values[f"sma_{period}"] = prices[-1] if prices else 0

        return sma_values

    def _calculate_ema(
        self, prices: List[float], periods: List[int]
    ) -> Dict[str, float]:
        """Calculate Exponential Moving Averages"""
        ema_values = {}

        for period in periods:
            if len(prices) >= period:
                ema = self._calculate_ema_single(prices, period)
                ema_values[f"ema_{period}"] = ema
            else:
                ema_values[f"ema_{period}"] = prices[-1] if prices else 0

        return ema_values

    def _calculate_ema_single(self, prices: List[float], period: int) -> float:
        """Calculate single EMA"""
        if not prices:
            return 0

        multiplier = 2 / (period + 1)
        ema = prices[0]

        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema

    def _evaluate_symbol_signals(
        self, symbol: str, analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate technical signals for a symbol"""
        signals = {"action": "hold", "strength": 0, "reasoning": []}

        current_price = analysis.get("current_price", 0)
        rsi = analysis.get("rsi", 50)
        macd = analysis.get("macd", 0)
        macd_signal = analysis.get("macd_signal", 0)
        bb_upper = analysis.get("bb_upper", 0)
        bb_lower = analysis.get("bb_lower", 0)
        sma_20 = analysis.get("sma_20", 0)
        sma_50 = analysis.get("sma_50", 0)

        buy_signals = 0
        sell_signals = 0

        # RSI signals
        if rsi < 30:
            buy_signals += 1
            signals["reasoning"].append(f"RSI oversold ({rsi:.1f})")
        elif rsi > 70:
            sell_signals += 1
            signals["reasoning"].append(f"RSI overbought ({rsi:.1f})")

        # MACD signals
        if macd > macd_signal:
            buy_signals += 1
            signals["reasoning"].append("MACD bullish")
        else:
            sell_signals += 1
            signals["reasoning"].append("MACD bearish")

        # Bollinger Bands signals
        if current_price < bb_lower:
            buy_signals += 1
            signals["reasoning"].append("Price below lower BB")
        elif current_price > bb_upper:
            sell_signals += 1
            signals["reasoning"].append("Price above upper BB")

        # Moving average signals
        if current_price > sma_20 and sma_20 > sma_50:
            buy_signals += 1
            signals["reasoning"].append("Above rising MA")
        elif current_price < sma_20 and sma_20 < sma_50:
            sell_signals += 1
            signals["reasoning"].append("Below falling MA")

        # Determine action
        if buy_signals >= 3:
            signals["action"] = "buy"
            signals["strength"] = buy_signals / 5.0
        elif sell_signals >= 3:
            signals["action"] = "sell"
            signals["strength"] = sell_signals / 5.0
        else:
            signals["action"] = "hold"
            signals["strength"] = 0.5

        return signals

    def _calculate_overall_confidence(self) -> float:
        """Calculate overall confidence in technical signals"""
        if not self.technical_signals:
            return 0.0

        total_confidence = 0.0
        count = 0

        for symbol, analysis in self.technical_signals.items():
            signal = analysis.get("signal", {})
            strength = signal.get("strength", 0)

            if signal.get("action") != "hold":
                total_confidence += strength
                count += 1

        return total_confidence / count if count > 0 else 0.0

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

    async def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "running": self.running,
            "symbols_analyzed": len(self.technical_signals),
            "signals_generated": len(
                [
                    s
                    for s in self.technical_signals.values()
                    if s.get("signal", {}).get("action") != "hold"
                ]
            ),
            "overall_confidence": self._calculate_overall_confidence(),
            "status": "active" if self.running else "stopped",
        }
