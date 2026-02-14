"""
Integration tests for VOLT Trading Agents
Tests that agents work with real exchange connections
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
import pandas as pd

from src.core.config_manager import ConfigManager
from src.agents.market_data_agent import MarketDataAgent
from src.agents.technical_agent import TechnicalAnalysisAgent
from src.agents.simple_agents import ExecutionAgent, MonitoringAgent
from src.strategies.volt_strategy import VOLTStrategy


@pytest.mark.asyncio
async def test_market_data_agent_with_mock_exchange():
    """Test MarketDataAgent with mocked exchange"""
    config_manager = ConfigManager()

    # Mock exchange
    mock_exchange = MagicMock()
    mock_exchange.get_ticker = AsyncMock(return_value=50000.0)
    mock_exchange.get_ohlcv = AsyncMock(
        return_value=[
            [1000000, 49000, 50000, 48900, 49500, 1000],
            [1000001, 49500, 50500, 49400, 50000, 1100],
        ]
    )

    agent = MarketDataAgent(config_manager, mock_exchange)
    await agent.initialize()

    # Fetch data for one symbol
    data = await agent._fetch_symbol_data("BTC/USDT")

    assert data is not None
    assert "price" in data
    assert data["price"] == 50000.0
    assert "volume" in data
    assert "change_24h" in data


@pytest.mark.asyncio
async def test_technical_agent_with_strategy():
    """Test TechnicalAnalysisAgent with VOLTStrategy"""
    config_manager = ConfigManager()
    strategy = VOLTStrategy(config_manager)
    await strategy.initialize()

    agent = TechnicalAnalysisAgent(config_manager, strategy)
    await agent.initialize()

    # Create sample market data
    sample_data = pd.DataFrame(
        {
            "timestamp": pd.date_range(start="2024-01-01", periods=100, freq="5min"),
            "open": [50000 + i * 10 for i in range(100)],
            "high": [50100 + i * 10 for i in range(100)],
            "low": [49900 + i * 10 for i in range(100)],
            "close": [50050 + i * 10 for i in range(100)],
            "volume": [1000 + i * 5 for i in range(100)],
        }
    )

    # Set market data
    agent.set_market_data({"BTC/USDT": sample_data})

    # Run analysis
    await agent._analyze_markets()

    # Check that analysis was performed
    assert "BTC/USDT" in agent.technical_signals
    assert "rsi" in agent.technical_signals["BTC/USDT"]


@pytest.mark.asyncio
async def test_execution_agent_with_mock_exchange():
    """Test ExecutionAgent with mocked exchange"""
    config_manager = ConfigManager()

    # Mock exchange
    mock_exchange = MagicMock()
    mock_exchange.create_market_buy_order = AsyncMock(
        return_value={
            "id": "order123",
            "price": 50000.0,
            "filled": 0.1,
            "fee": {"cost": 5.0, "currency": "USDT"},
        }
    )

    agent = ExecutionAgent(config_manager, mock_exchange)
    await agent.initialize()

    # Execute buy order
    result = await agent.execute_order(
        {"symbol": "BTC/USDT", "side": "buy", "amount": 0.1}
    )

    assert result["status"] == "filled"
    assert result["order_id"] == "order123"
    assert result["filled_price"] == 50000.0


@pytest.mark.asyncio
async def test_execution_agent_handles_missing_exchange():
    """Test ExecutionAgent gracefully handles missing exchange"""
    config_manager = ConfigManager()

    agent = ExecutionAgent(config_manager, exchange=None)
    await agent.initialize()

    # Try to execute order
    result = await agent.execute_order(
        {"symbol": "BTC/USDT", "side": "buy", "amount": 0.1}
    )

    assert result["status"] == "failed"
    assert "error" in result


@pytest.mark.asyncio
async def test_monitoring_agent_with_exchange():
    """Test MonitoringAgent with exchange"""
    config_manager = ConfigManager()

    # Mock exchange
    mock_exchange = MagicMock()
    mock_exchange.get_balance = AsyncMock(
        return_value={"USDT": {"free": 10000.0, "used": 1000.0, "total": 11000.0}}
    )

    agent = MonitoringAgent(config_manager, mock_exchange)
    await agent.initialize()
    await agent.start()

    # Get health
    health = await agent.get_health()

    assert health["system_status"] == "healthy"
    assert "uptime_seconds" in health
    assert health["uptime_seconds"] >= 0

    await agent.stop()


@pytest.mark.asyncio
async def test_technical_agent_uses_strategy_parameters():
    """Test that TechnicalAnalysisAgent uses VOLTStrategy parameters"""
    config_manager = ConfigManager()
    strategy = VOLTStrategy(config_manager)
    await strategy.initialize()

    agent = TechnicalAnalysisAgent(config_manager, strategy)
    await agent.initialize()

    # Verify agent uses strategy parameters
    assert agent.rsi_period == strategy.rsi_period
    assert agent.rsi_oversold == strategy.rsi_oversold
    assert agent.rsi_overbought == strategy.rsi_overbought


@pytest.mark.asyncio
async def test_market_data_agent_validation():
    """Test MarketDataAgent data validation"""
    config_manager = ConfigManager()
    agent = MarketDataAgent(config_manager, exchange=None)
    await agent.initialize()

    # Test valid data
    valid_data = {
        "price": 50000.0,
        "volume": 1000.0,
        "timestamp": "2024-01-01T00:00:00",
    }
    assert agent._validate_symbol_data(valid_data) is True

    # Test invalid data (missing fields)
    invalid_data = {"price": 50000.0}
    assert agent._validate_symbol_data(invalid_data) is False

    # Test invalid data (negative price)
    invalid_data2 = {"price": -50000.0, "volume": 1000.0, "timestamp": "2024-01-01"}
    assert agent._validate_symbol_data(invalid_data2) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
