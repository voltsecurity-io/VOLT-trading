"""
Technical Analysis Agent
Handles technical indicator calculations and analysis
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

from src.core.config_manager import ConfigManager
from src.utils.logger import get_logger
from src.strategies.volt_strategy import VOLTStrategy


class TechnicalAnalysisAgent:
    """Agent responsible for technical analysis"""

    def __init__(
        self,
        config_manager: ConfigManager,
        strategy: Optional[VOLTStrategy] = None,
    ):
        self.config_manager = config_manager
        self.strategy = strategy
        self.logger = get_logger(__name__)

        self.running = False
        self.technical_signals = {}
        self.market_data_cache = {}

    async def initialize(self):
        """Initialize technical analysis agent"""
        self.logger.info("📈 Initializing Technical Analysis Agent...")

        if not self.strategy:
            self.logger.warning(
                "⚠️ No strategy provided - using default indicator parameters"
            )
            # Fallback to default parameters if no strategy
            self.rsi_period = 14
            self.rsi_oversold = 30
            self.rsi_overbought = 70
        else:
            # Use strategy's parameters
            self.rsi_period = self.strategy.rsi_period
            self.rsi_oversold = self.strategy.rsi_oversold
            self.rsi_overbought = self.strategy.rsi_overbought

        self.logger.info("📊 Technical analysis configured")

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

    def set_market_data(self, market_data: Dict[str, pd.DataFrame]):
        """Set market data for analysis (called by orchestrator or trading engine)"""
        self.market_data_cache = market_data

    async def _analyze_markets(self):
        """Perform technical analysis on all symbols"""
        if not self.market_data_cache:
            self.logger.debug("No market data available for analysis yet")
            return

        for symbol, df in self.market_data_cache.items():
            try:
                # Use strategy's indicator calculation if available
                if self.strategy:
                    df_with_indicators = self.strategy._calculate_indicators(df)
                else:
                    # Fallback: basic calculation
                    df_with_indicators = self._calculate_basic_indicators(df)

                # Store analysis results
                self.technical_signals[symbol] = self._extract_indicators(
                    df_with_indicators
                )

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

    def _extract_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract latest indicator values from DataFrame"""
        if len(df) == 0:
            return {}

        latest = df.iloc[-1]
        indicators = {}

        # Extract all available indicators
        for col in df.columns:
            if col not in ["timestamp", "open", "high", "low", "close", "volume"]:
                try:
                    indicators[col] = float(latest[col]) if pd.notna(latest[col]) else 0.0
                except (ValueError, TypeError):
                    indicators[col] = 0.0

        # Add current price
        indicators["current_price"] = float(latest["close"])

        # Add price changes
        if len(df) > 1:
            previous = df.iloc[-2]
            indicators["price_change_1"] = (
                (latest["close"] - previous["close"]) / previous["close"]
            )
        if len(df) > 5:
            prev_5 = df.iloc[-6]
            indicators["price_change_5"] = (
                (latest["close"] - prev_5["close"]) / prev_5["close"]
            )

        return indicators

    def _calculate_basic_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fallback basic indicator calculation if no strategy available"""
        df = df.copy()

        # Basic RSI
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))

        # Basic moving averages
        df["sma_20"] = df["close"].rolling(window=20).mean()
        df["sma_50"] = df["close"].rolling(window=50).mean()

        # Basic MACD
        ema_12 = df["close"].ewm(span=12).mean()
        ema_26 = df["close"].ewm(span=26).mean()
        df["macd"] = ema_12 - ema_26
        df["macd_signal"] = df["macd"].ewm(span=9).mean()

        # Bollinger Bands
        sma_20 = df["close"].rolling(window=20).mean()
        std_20 = df["close"].rolling(window=20).std()
        df["bb_upper"] = sma_20 + (std_20 * 2)
        df["bb_middle"] = sma_20
        df["bb_lower"] = sma_20 - (std_20 * 2)

        # Volume ratio
        df["volume_sma"] = df["volume"].rolling(window=20).mean()
        df["volume_ratio"] = df["volume"] / df["volume_sma"]

        return df

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
        volume_ratio = analysis.get("volume_ratio", 1.0)

        buy_signals = 0
        sell_signals = 0

        # RSI signals
        if rsi < self.rsi_oversold:
            buy_signals += 1
            signals["reasoning"].append(f"RSI oversold ({rsi:.1f})")
        elif rsi > self.rsi_overbought:
            sell_signals += 1
            signals["reasoning"].append(f"RSI overbought ({rsi:.1f})")

        # MACD signals
        if macd > macd_signal:
            buy_signals += 1
            signals["reasoning"].append("MACD bullish")
        else:
            sell_signals += 1
            signals["reasoning"].append("MACD bearish")

        # Bollinger Bands signals (only if we have valid values)
        if bb_lower > 0 and bb_upper > 0:
            if current_price < bb_lower:
                buy_signals += 1
                signals["reasoning"].append("Price below lower BB")
            elif current_price > bb_upper:
                sell_signals += 1
                signals["reasoning"].append("Price above upper BB")

        # Moving average signals (only if we have valid values)
        if sma_20 > 0 and sma_50 > 0:
            if current_price > sma_20 and sma_20 > sma_50:
                buy_signals += 1
                signals["reasoning"].append("Above rising MA")
            elif current_price < sma_20 and sma_20 < sma_50:
                sell_signals += 1
                signals["reasoning"].append("Below falling MA")

        # Volume confirmation
        if volume_ratio > 1.2:
            signals["reasoning"].append(f"Volume spike ({volume_ratio:.2f}x)")

        # Determine action
        if buy_signals >= 3:
            signals["action"] = "buy"
            signals["strength"] = min(buy_signals / 5.0, 1.0)
        elif sell_signals >= 3:
            signals["action"] = "sell"
            signals["strength"] = min(sell_signals / 5.0, 1.0)
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
