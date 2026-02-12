"""
VOLT Trading Risk Manager
Advanced risk management system
"""

import asyncio
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from src.core.config_manager import ConfigManager
from src.utils.logger import get_logger


class RiskManager:
    """Advanced Risk Management for VOLT Trading"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        self.risk_config = config_manager.get_risk_config()

        # Risk parameters
        self.max_position_size = self.risk_config.get("max_leverage", 1.0)
        self.correlation_limit = self.risk_config.get("correlation_limit", 0.7)
        self.max_drawdown = config_manager.get("trading.max_drawdown", 0.15)
        self.volatility_adjustment = self.risk_config.get("volatility_adjustment", True)

        # Tracking
        self.daily_loss = 0.0
        self.daily_trades = 0
        self.last_reset = datetime.now().date()

    async def initialize(self):
        """Initialize risk manager"""
        self.logger.info("🛡️ Initializing Risk Manager...")

        # Load historical data for correlation analysis
        await self._load_correlation_data()

        self.logger.info("✅ Risk Manager initialized")

    async def assess_risk(
        self, signal: Dict[str, Any], positions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess risk for trading signal"""

        # Reset daily counters if needed
        self._reset_daily_counters()

        assessment = {
            "approved": False,
            "position_size": 0.0,
            "risk_score": 0.0,
            "reason": "",
        }

        try:
            # Basic risk checks
            if not await self._basic_risk_check(signal):
                assessment["reason"] = "Failed basic risk check"
                return assessment

            # Position size check
            if not await self._position_size_check(signal):
                assessment["reason"] = "Position size too large"
                return assessment

            # Correlation check
            if not await self._correlation_check(signal, positions):
                assessment["reason"] = "High correlation with existing positions"
                return assessment

            # Drawdown check
            if not await self._drawdown_check():
                assessment["reason"] = "Maximum drawdown exceeded"
                return assessment

            # Volatility adjustment
            adjusted_size = await self._volatility_adjustment(signal)

            # Calculate final position size
            base_size = signal.get("position_size", 0.025)
            final_size = min(base_size, adjusted_size, self.max_position_size)

            # Calculate risk score
            risk_score = self._calculate_risk_score(signal, positions)

            assessment.update(
                {
                    "approved": True,
                    "position_size": final_size,
                    "risk_score": risk_score,
                    "reason": "Risk assessment passed",
                }
            )

            self.logger.info(
                f"✅ Risk approved for {signal['symbol']} - "
                f"Size: {final_size:.3f}, Risk Score: {risk_score:.2f}"
            )

        except Exception as e:
            self.logger.error(f"❌ Risk assessment error: {e}")
            assessment["reason"] = f"Risk assessment error: {e}"

        return assessment

    async def _basic_risk_check(self, signal: Dict[str, Any]) -> bool:
        """Basic risk validation"""

        # Check signal validity
        required_fields = [
            "symbol",
            "action",
            "entry_price",
            "stop_loss",
            "take_profit",
        ]
        if not all(field in signal for field in required_fields):
            self.logger.warning("⚠️ Signal missing required fields")
            return False

        # Check risk/reward ratio
        entry_price = signal["entry_price"]
        stop_loss = signal["stop_loss"]
        take_profit = signal["take_profit"]

        if signal["action"] == "buy":
            risk = entry_price - stop_loss
            reward = take_profit - entry_price
        else:
            risk = stop_loss - entry_price
            reward = entry_price - take_profit

        if risk <= 0:
            self.logger.warning("⚠️ Invalid stop loss configuration")
            return False

        reward_risk_ratio = reward / risk
        if reward_risk_ratio < 1.5:  # Minimum 1.5:1 ratio
            self.logger.warning(f"⚠️ Poor risk/reward ratio: {reward_risk_ratio:.2f}")
            return False

        # Check signal strength
        if signal.get("confidence", 0) < 0.6:
            self.logger.warning("⚠️ Low signal confidence")
            return False

        return True

    async def _position_size_check(self, signal: Dict[str, Any]) -> bool:
        """Check if position size is within limits"""
        position_size = signal.get("position_size", 0.0)

        if position_size > self.max_position_size:
            self.logger.warning(
                f"⚠️ Position size {position_size:.3f} exceeds limit {self.max_position_size:.3f}"
            )
            return False

        return True

    async def _correlation_check(
        self, signal: Dict[str, Any], positions: Dict[str, Any]
    ) -> bool:
        """Check correlation with existing positions"""
        if not positions:
            return True

        signal_symbol = signal["symbol"]

        # Simple correlation check based on asset class
        for pos_symbol, position in positions.items():
            if position.get("quantity", 0) == 0:
                continue

            # Check if assets are highly correlated
            correlation = self._get_correlation(signal_symbol, pos_symbol)
            if correlation > self.correlation_limit:
                self.logger.warning(
                    f"⚠️ High correlation ({correlation:.2f}) between {signal_symbol} and {pos_symbol}"
                )
                return False

        return True

    async def _drawdown_check(self) -> bool:
        """Check if current drawdown is within limits"""
        # This would typically track portfolio value over time
        # For now, use daily loss as a simple proxy
        if abs(self.daily_loss) > self.max_drawdown:
            self.logger.warning(
                f"⚠️ Daily loss {abs(self.daily_loss):.3f} exceeds limit"
            )
            return False

        return True

    async def _volatility_adjustment(self, signal: Dict[str, Any]) -> float:
        """Adjust position size based on volatility"""
        if not self.volatility_adjustment:
            return self.max_position_size

        # Get volatility for the symbol (simplified)
        volatility = await self._get_symbol_volatility(signal["symbol"])

        # Inverse volatility scaling - higher volatility = smaller position
        volatility_factor = 1.0 / (1.0 + volatility)

        adjusted_size = self.max_position_size * volatility_factor

        self.logger.info(
            f"📊 Volatility adjustment for {signal['symbol']}: "
            f"Vol={volatility:.3f}, Factor={volatility_factor:.3f}, Size={adjusted_size:.3f}"
        )

        return adjusted_size

    def _calculate_risk_score(
        self, signal: Dict[str, Any], positions: Dict[str, Any]
    ) -> float:
        """Calculate overall risk score (0-1, higher = riskier)"""

        score = 0.0

        # Position size contribution
        size_score = signal.get("position_size", 0.025) / self.max_position_size
        score += size_score * 0.3

        # Signal confidence contribution (inverse)
        confidence = signal.get("confidence", 0.6)
        confidence_score = 1 - confidence
        score += confidence_score * 0.2

        # Portfolio concentration contribution
        if positions:
            active_positions = len(
                [p for p in positions.values() if p.get("quantity", 0) != 0]
            )
            concentration_score = min(active_positions / 10, 1.0)  # Max at 10 positions
            score += concentration_score * 0.2

        # Volatility contribution
        volatility_contribution = 0.2  # Placeholder

        # Daily trading activity contribution
        activity_score = min(self.daily_trades / 20, 1.0)  # Max at 20 trades/day
        score += activity_score * 0.1

        return min(score, 1.0)

    def _get_correlation(self, symbol1: str, symbol2: str) -> float:
        """Get correlation between two symbols (simplified)"""
        # Simplified correlation based on asset classes
        if "BTC" in symbol1 and "ETH" in symbol2:
            return 0.8
        elif "ETH" in symbol1 and "BTC" in symbol2:
            return 0.8
        elif "BTC" in symbol1 and "BTC" in symbol2:
            return 1.0
        elif "ETH" in symbol1 and "ETH" in symbol2:
            return 1.0
        else:
            return 0.3  # Low correlation for different asset types

    async def _get_symbol_volatility(self, symbol: str) -> float:
        """Get volatility for a symbol (simplified)"""
        # Simplified volatility calculation
        volatilities = {
            "BTC/USDT": 0.03,
            "ETH/USDT": 0.04,
            "BNB/USDT": 0.035,
            "SOL/USDT": 0.06,
            "AVAX/USDT": 0.055,
            "MATIC/USDT": 0.05,
        }

        return volatilities.get(symbol, 0.04)

    async def _load_correlation_data(self):
        """Load historical correlation data"""
        # In production, load actual correlation matrix
        self.correlation_matrix = {}

    def _reset_daily_counters(self):
        """Reset daily counters if it's a new day"""
        today = datetime.now().date()
        if today > self.last_reset:
            self.daily_loss = 0.0
            self.daily_trades = 0
            self.last_reset = today
            self.logger.info("🔄 Daily risk counters reset")

    def update_daily_metrics(self, pnl: float):
        """Update daily metrics after trade"""
        self.daily_loss += pnl
        self.daily_trades += 1

    def get_risk_metrics(self) -> Dict[str, Any]:
        """Get current risk metrics"""
        return {
            "daily_loss": self.daily_loss,
            "daily_trades": self.daily_trades,
            "max_position_size": self.max_position_size,
            "correlation_limit": self.correlation_limit,
            "max_drawdown": self.max_drawdown,
            "last_reset": self.last_reset.isoformat(),
        }


if __name__ == "__main__":
    # Test risk manager
    config_manager = ConfigManager()
    risk_manager = RiskManager(config_manager)
    print("✅ Risk Manager test completed")
