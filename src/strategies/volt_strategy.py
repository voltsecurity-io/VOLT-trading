"""
VOLT Trading Strategy
Enhanced version of X1Nano-Superior with advanced features
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.core.config_manager import ConfigManager
from src.utils.logger import get_logger
from src.collectors.volatility_collector import VolatilityCollector


class VOLTStrategy:
    """Advanced VOLT Trading Strategy"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        self.config = config_manager.get_trading_config()

        # Strategy parameters
        self.rsi_period = 14
        self.rsi_overbought = 65  # Lowered from 70 - sell earlier for more activity
        self.rsi_oversold = 35    # Raised from 30 - buy earlier for more activity

        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9

        self.bb_period = 20
        self.bb_std = 2

        # Risk parameters
        self.max_position_size = self.config.get("max_position_size", 0.10)
        self.stop_loss = self.config.get("stop_loss", 0.05)
        self.take_profit = self.config.get("take_profit", 0.10)
        
        # Phase 0: Volatility collector for dynamic thresholds
        self.volatility_collector = VolatilityCollector()
        self.current_vix = 20.0  # Default
        self.vix_regime = "NORMAL"

    async def initialize(self):
        """Initialize strategy components"""
        self.logger.info("🧠 Initializing VOLT Strategy...")

        # Load ML models if enabled
        if self.config_manager.get("ml_models.lstm_enabled", False):
            await self._load_lstm_model()

        if self.config_manager.get("ml_models.sentiment_analysis", False):
            await self._load_sentiment_model()

        self.logger.info("✅ VOLT Strategy initialized")

    async def generate_signals(
        self, market_data: Dict[str, pd.DataFrame]
    ) -> List[Dict[str, Any]]:
        """Generate trading signals from market data"""
        signals = []

        for symbol, df in market_data.items():
            try:
                # Calculate technical indicators
                df_with_indicators = self._calculate_indicators(df)

                # Generate signal for this symbol
                signal = self._analyze_symbol(symbol, df_with_indicators)

                if signal:
                    signals.append(signal)

            except Exception as e:
                self.logger.error(f"❌ Error analyzing {symbol}: {e}")

        return signals

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        df = df.copy()

        # RSI
        df["rsi"] = self._calculate_rsi(df["close"], self.rsi_period)

        # MACD
        macd = self._calculate_macd(df["close"])
        df["macd"] = macd["macd"]
        df["macd_signal"] = macd["signal"]
        df["macd_histogram"] = macd["histogram"]

        # Bollinger Bands
        bb = self._calculate_bollinger_bands(df["close"], self.bb_period, self.bb_std)
        df["bb_upper"] = bb["upper"]
        df["bb_middle"] = bb["middle"]
        df["bb_lower"] = bb["lower"]

        # Moving Averages
        df["sma_20"] = df["close"].rolling(window=20).mean()
        df["sma_50"] = df["close"].rolling(window=50).mean()
        df["ema_12"] = df["close"].ewm(span=12).mean()
        df["ema_26"] = df["close"].ewm(span=26).mean()

        # Volume indicators
        df["volume_sma"] = df["volume"].rolling(window=20).mean()
        df["volume_ratio"] = df["volume"] / df["volume_sma"]

        # Volatility
        df["volatility"] = df["close"].rolling(window=20).std()
        df["atr"] = self._calculate_atr(df)

        # Price change
        df["price_change"] = df["close"].pct_change()
        df["price_change_abs"] = abs(df["price_change"])

        return df

    def _analyze_symbol(
        self, symbol: str, df: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """Analyze symbol and generate signal"""
        if len(df) < 50:
            return None

        latest = df.iloc[-1]
        previous = df.iloc[-2]

        # Buy conditions - scored individually (no longer requires ALL to be true)
        buy_score = 0
        buy_total = 6
        if latest["rsi"] < self.rsi_oversold:
            buy_score += 1.5  # Strong indicator
        elif latest["rsi"] < 40:
            buy_score += 0.5  # Approaching oversold
        if latest["macd"] > latest["macd_signal"]:
            buy_score += 1.0
        if previous["macd"] <= previous["macd_signal"]:  # Fresh crossover
            buy_score += 1.0
        if latest["close"] < latest["bb_lower"]:
            buy_score += 1.0
        elif latest["close"] < latest["bb_middle"]:
            buy_score += 0.3  # Below middle band
        if latest["volume_ratio"] > 1.2:
            buy_score += 0.5
        if latest["close"] > latest["sma_50"]:
            buy_score += 0.5  # Trend confirmation (bonus, not required)

        # Sell conditions - scored individually
        sell_score = 0
        sell_total = 5
        if latest["rsi"] > self.rsi_overbought:
            sell_score += 1.5
        elif latest["rsi"] > 60:
            sell_score += 0.5
        if latest["macd"] < latest["macd_signal"]:
            sell_score += 1.0
        if previous["macd"] >= previous["macd_signal"]:  # Fresh crossover
            sell_score += 1.0
        if latest["close"] > latest["bb_upper"]:
            sell_score += 1.0
        if latest["volume_ratio"] > 1.2:
            sell_score += 0.5

        # Determine signal - minimum 3.0 score required
        signal_strength = 0
        signal_action = None

        if buy_score >= 3.0 and buy_score > sell_score:
            signal_action = "buy"
            signal_strength = min(buy_score / buy_total, 1.0)

        elif sell_score >= 3.0 and sell_score > buy_score:
            signal_action = "sell"
            signal_strength = min(sell_score / sell_total, 1.0)

        # Phase 0: Dynamic threshold based on VIX regime
        threshold = self._get_adaptive_threshold()
        
        if signal_action and signal_strength > threshold:
            # Calculate position size using Kelly Criterion
            win_rate = self._estimate_win_rate(symbol, df)
            avg_win_loss = self._estimate_avg_win_loss(df)
            kelly_fraction = self._calculate_kelly_criterion(win_rate, avg_win_loss)

            # Calculate entry and exit prices
            entry_price = latest["close"]
            stop_loss_price = (
                entry_price * (1 - self.stop_loss)
                if signal_action == "buy"
                else entry_price * (1 + self.stop_loss)
            )
            take_profit_price = (
                entry_price * (1 + self.take_profit)
                if signal_action == "buy"
                else entry_price * (1 - self.take_profit)
            )

            return {
                "symbol": symbol,
                "action": signal_action,
                "strength": signal_strength,
                "entry_price": entry_price,
                "stop_loss": stop_loss_price,
                "take_profit": take_profit_price,
                "position_size": min(kelly_fraction, self.max_position_size),
                "confidence": signal_strength,
                "reasoning": self._generate_reasoning(signal_action, latest, df),
                "timestamp": datetime.now().isoformat(),
            }

        return None

    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_macd(self, prices: pd.Series) -> Dict[str, pd.Series]:
        """Calculate MACD indicator"""
        ema_fast = prices.ewm(span=self.macd_fast).mean()
        ema_slow = prices.ewm(span=self.macd_slow).mean()
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=self.macd_signal).mean()
        histogram = macd - signal

        return {"macd": macd, "signal": signal, "histogram": histogram}

    def _calculate_bollinger_bands(
        self, prices: pd.Series, period: int, std: float
    ) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands"""
        middle = prices.rolling(window=period).mean()
        rolling_std = prices.rolling(window=period).std()
        upper = middle + (rolling_std * std)
        lower = middle - (rolling_std * std)

        return {"upper": upper, "middle": middle, "lower": lower}

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high_low = df["high"] - df["low"]
        high_close = abs(df["high"] - df["close"].shift())
        low_close = abs(df["low"] - df["close"].shift())

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()

        return atr

    def _estimate_win_rate(self, symbol: str, df: pd.DataFrame) -> float:
        """Estimate historical win rate"""
        # Simplified win rate estimation
        price_changes = df["price_change"].dropna()
        wins = len(price_changes[price_changes > 0])
        total = len(price_changes)

        return wins / total if total > 0 else 0.5

    def _estimate_avg_win_loss(self, df: pd.DataFrame) -> float:
        """Estimate average win/loss ratio"""
        price_changes = df["price_change"].dropna()
        wins = price_changes[price_changes > 0]
        losses = price_changes[price_changes < 0]

        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 0.01

        return avg_win / avg_loss if avg_loss > 0 else 2.0

    def _calculate_kelly_criterion(self, win_rate: float, avg_win_loss: float) -> float:
        """Calculate Kelly Criterion position size"""
        if avg_win_loss <= 0:
            return 0.01

        kelly = (win_rate * (avg_win_loss + 1) - 1) / avg_win_loss
        kelly = max(0.01, min(kelly, 0.25))  # Cap at 25% minimum 1%

        return kelly

    def _generate_reasoning(
        self, action: str, latest: pd.Series, df: pd.DataFrame
    ) -> str:
        """Generate reasoning for signal"""
        reasons = []

        if action == "buy":
            if latest["rsi"] < self.rsi_oversold:
                reasons.append(f"RSI oversold ({latest['rsi']:.1f})")
            if latest["macd"] > latest["macd_signal"]:
                reasons.append("MACD bullish crossover")
            if latest["close"] < latest["bb_lower"]:
                reasons.append("Price at lower Bollinger Band")
            if latest["volume_ratio"] > 1.2:
                reasons.append("Volume spike detected")
        else:
            if latest["rsi"] > self.rsi_overbought:
                reasons.append(f"RSI overbought ({latest['rsi']:.1f})")
            if latest["macd"] < latest["macd_signal"]:
                reasons.append("MACD bearish crossover")
            if latest["close"] > latest["bb_upper"]:
                reasons.append("Price at upper Bollinger Band")

        return "; ".join(reasons) if reasons else "Technical analysis signal"
    
    def _get_adaptive_threshold(self) -> float:
        """
        Phase 0: Dynamic signal strength threshold based on VIX regime
        
        Market Regimes:
        - VIX < 12: LOW (0.40 threshold - be aggressive)
        - VIX 12-20: NORMAL (0.45 threshold - standard)
        - VIX 20-30: ELEVATED (0.55 threshold - be cautious)
        - VIX > 30: PANIC (0.70 threshold - very selective)
        
        Returns:
            float: Threshold for signal_strength
        """
        
        # Use cached VIX or default
        vix = self.current_vix
        
        if vix < 12:
            threshold = 0.40
            regime = "LOW"
        elif vix < 20:
            threshold = 0.45
            regime = "NORMAL"
        elif vix < 30:
            threshold = 0.55
            regime = "ELEVATED"
        else:
            threshold = 0.70
            regime = "PANIC"
        
        # Log if regime changed
        if regime != self.vix_regime:
            self.logger.info(
                f"📊 VIX regime changed: {self.vix_regime} → {regime} "
                f"(VIX={vix:.1f}, threshold={threshold:.2f})"
            )
            self.vix_regime = regime
        
        return threshold
    
    async def update_vix_data(self):
        """
        Phase 0: Update VIX data for adaptive thresholds
        Call this periodically (e.g., every 5 minutes)
        """
        try:
            vix_data = await self.volatility_collector.get_vix_data()
            self.current_vix = vix_data['current_vix']
            self.vix_regime = vix_data['regime']
            
            self.logger.debug(
                f"📊 VIX updated: {self.current_vix:.1f} ({self.vix_regime})"
            )
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to update VIX: {e}, using cached value")

    async def _load_lstm_model(self):
        """Load LSTM model for price prediction"""
        self.logger.info("🧠 Loading LSTM model...")
        # In production, load actual ML model
        self.lstm_model = None

    async def _load_sentiment_model(self):
        """Load sentiment analysis model"""
        self.logger.info("💭 Loading sentiment model...")
        # In production, load actual sentiment model
        self.sentiment_model = None


if __name__ == "__main__":
    # Test strategy
    config_manager = ConfigManager()
    strategy = VOLTStrategy(config_manager)
    print("✅ VOLT Strategy test completed")
