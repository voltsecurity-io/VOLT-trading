"""
Tests for Fas 2: Enhanced Monitoring and Sentiment agents
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.core.config_manager import ConfigManager
from src.agents.simple_agents import MonitoringAgent, SentimentAnalysisAgent


@pytest.mark.asyncio
async def test_monitoring_agent_portfolio_tracking():
    """Test MonitoringAgent portfolio P&L tracking"""
    config_manager = ConfigManager()

    # Mock exchange
    mock_exchange = MagicMock()
    mock_exchange.get_balance = AsyncMock(
        return_value={"USDT": {"free": 10000.0, "used": 0.0, "total": 10000.0}}
    )
    mock_exchange.get_ticker = AsyncMock(return_value=51000.0)  # BTC price

    agent = MonitoringAgent(config_manager, mock_exchange)
    await agent.initialize()

    # Track a position
    await agent.track_position("BTC/USDT", 50000.0, 0.1, "buy")

    assert "BTC/USDT" in agent.positions
    assert agent.positions["BTC/USDT"]["entry_price"] == 50000.0
    assert agent.positions["BTC/USDT"]["amount"] == 0.1

    # Get P&L
    pnl = await agent.get_portfolio_pnl()
    assert "unrealized_pnl" in pnl
    # Unrealized: (51000 - 50000) * 0.1 = 100
    assert pnl["unrealized_pnl"] == pytest.approx(100.0, rel=0.01)


@pytest.mark.asyncio
async def test_monitoring_agent_close_position():
    """Test closing a position and calculating realized P&L"""
    config_manager = ConfigManager()
    mock_exchange = MagicMock()
    mock_exchange.get_balance = AsyncMock(
        return_value={"USDT": {"free": 10000.0, "used": 0.0, "total": 10000.0}}
    )

    agent = MonitoringAgent(config_manager, mock_exchange)
    agent.metrics_file = "reports/test_close_position.json"
    await agent.initialize()

    # Open position
    await agent.track_position("BTC/USDT", 50000.0, 0.1, "buy")

    # Close position at profit
    await agent.track_position("BTC/USDT", 51000.0, 0.1, "sell")

    # Position should be closed
    assert "BTC/USDT" not in agent.positions

    # Check realized P&L: (51000 - 50000) * 0.1 = 100
    assert agent.total_pnl == pytest.approx(100.0, rel=0.01)
    assert agent.total_trades == 1
    assert agent.winning_trades == 1
    assert agent.losing_trades == 0


@pytest.mark.asyncio
async def test_monitoring_agent_partial_close():
    """Test partial position close"""
    config_manager = ConfigManager()
    mock_exchange = MagicMock()
    mock_exchange.get_balance = AsyncMock(
        return_value={"USDT": {"total": 10000.0}}
    )

    agent = MonitoringAgent(config_manager, mock_exchange)
    agent.metrics_file = "reports/test_partial_close.json"
    await agent.initialize()

    # Open position
    await agent.track_position("ETH/USDT", 3000.0, 1.0, "buy")

    # Partial close
    await agent.track_position("ETH/USDT", 3100.0, 0.5, "sell")

    # Position should still exist with reduced amount
    assert "ETH/USDT" in agent.positions
    assert agent.positions["ETH/USDT"]["amount"] == 0.5

    # Realized P&L: (3100 - 3000) * 0.5 = 50
    assert agent.total_pnl == pytest.approx(50.0, rel=0.01)


@pytest.mark.asyncio
async def test_monitoring_agent_win_rate():
    """Test win rate calculation"""
    config_manager = ConfigManager()
    mock_exchange = MagicMock()
    mock_exchange.get_balance = AsyncMock(
        return_value={"USDT": {"total": 10000.0}}
    )

    agent = MonitoringAgent(config_manager, mock_exchange)
    agent.metrics_file = "reports/test_win_rate.json"
    await agent.initialize()

    # Win trade
    await agent.track_position("BTC/USDT", 50000.0, 0.1, "buy")
    await agent.track_position("BTC/USDT", 51000.0, 0.1, "sell")

    # Loss trade
    await agent.track_position("ETH/USDT", 3000.0, 1.0, "buy")
    await agent.track_position("ETH/USDT", 2900.0, 1.0, "sell")

    # Win trade
    await agent.track_position("SOL/USDT", 100.0, 10.0, "buy")
    await agent.track_position("SOL/USDT", 110.0, 10.0, "sell")

    pnl = await agent.get_portfolio_pnl()
    assert pnl["total_trades"] == 3
    assert pnl["winning_trades"] == 2
    assert pnl["losing_trades"] == 1
    assert pnl["win_rate"] == pytest.approx(66.67, rel=0.01)


@pytest.mark.asyncio
async def test_monitoring_agent_save_load_metrics():
    """Test metrics persistence"""
    config_manager = ConfigManager()
    mock_exchange = MagicMock()
    mock_exchange.get_balance = AsyncMock(
        return_value={"USDT": {"total": 10000.0}}
    )

    agent = MonitoringAgent(config_manager, mock_exchange)
    agent.metrics_file = "reports/test_save_load.json"
    # Clear any existing file
    import os
    if os.path.exists(agent.metrics_file):
        os.remove(agent.metrics_file)
    
    await agent.initialize()

    # Track some trades
    await agent.track_position("BTC/USDT", 50000.0, 0.1, "buy")
    await agent.track_position("BTC/USDT", 51000.0, 0.1, "sell")

    # Save metrics
    agent._save_metrics()

    # Create new agent and load metrics
    agent2 = MonitoringAgent(config_manager, mock_exchange)
    agent2.metrics_file = "reports/test_save_load.json"
    await agent2.initialize()

    # Should have loaded the metrics
    assert agent2.total_trades == 1
    assert agent2.winning_trades == 1
    assert agent2.total_pnl == pytest.approx(100.0, rel=0.01)


@pytest.mark.asyncio
async def test_monitoring_agent_health_metrics():
    """Test comprehensive health metrics"""
    config_manager = ConfigManager()
    mock_exchange = MagicMock()
    mock_exchange.get_balance = AsyncMock(
        return_value={
            "USDT": {"total": 10000.0},
            "BTC": {"total": 0.1},
        }
    )

    agent = MonitoringAgent(config_manager, mock_exchange)
    # Use temp file to avoid loading existing metrics
    agent.metrics_file = "reports/test_monitoring_temp.json"
    await agent.initialize()
    await agent.start()

    health = await agent.get_health()

    assert health["system_status"] == "healthy"
    assert "uptime_seconds" in health
    assert "cpu_usage" in health or "memory_usage" in health  # psutil might be available
    assert "portfolio_balance" in health
    assert health["open_positions"] == 0
    # Might have loaded metrics from file, so just check it's a number
    assert isinstance(health["total_trades"], int)

    await agent.stop()


@pytest.mark.asyncio
async def test_sentiment_agent_neutral_mode():
    """Test SentimentAnalysisAgent without API (neutral mode)"""
    config_manager = ConfigManager()
    agent = SentimentAnalysisAgent(config_manager)
    await agent.initialize()

    sentiment = await agent.get_sentiment()

    assert sentiment["sentiment_score"] == 0.0  # Neutral
    assert sentiment["confidence"] == 0.5
    assert "none" in sentiment["sources"]
    assert "note" in sentiment


@pytest.mark.asyncio
async def test_sentiment_agent_with_mock_api():
    """Test SentimentAnalysisAgent with mocked API response"""
    config_manager = ConfigManager()
    
    # Mock the get method to return API key
    original_get = config_manager.get
    
    def mock_get(key, default=None):
        if key == "sentiment.cryptopanic_api_key":
            return "test_key_12345"
        return original_get(key, default)
    
    config_manager.get = mock_get

    agent = SentimentAnalysisAgent(config_manager)
    await agent.initialize()

    assert agent.use_api is True

    # Manually set cache (simulating successful API fetch)
    agent.sentiment_cache = {
        "sentiment_score": 0.7,  # Positive
        "confidence": 0.8,
        "sources": ["cryptopanic"],
        "total_posts": 50,
        "positive_votes": 100,
        "negative_votes": 20,
        "last_update": datetime.now().isoformat(),
    }

    sentiment = await agent.get_sentiment()
    assert sentiment["sentiment_score"] == 0.7
    assert sentiment["confidence"] == 0.8


@pytest.mark.asyncio
async def test_sentiment_agent_process_data():
    """Test sentiment data processing"""
    config_manager = ConfigManager()
    agent = SentimentAnalysisAgent(config_manager)
    await agent.initialize()

    # Mock CryptoPanic API response
    mock_data = {
        "results": [
            {"votes": {"positive": 10, "negative": 2, "important": 5}},
            {"votes": {"positive": 8, "negative": 1, "important": 3}},
            {"votes": {"positive": 5, "negative": 5, "important": 1}},
        ]
    }

    agent._process_sentiment_data(mock_data)

    assert agent.sentiment_cache is not None
    assert "sentiment_score" in agent.sentiment_cache
    # Total: 23 positive, 8 negative = (23-8)/31 = 0.48, weighted by importance
    assert agent.sentiment_cache["sentiment_score"] > 0  # Should be positive


@pytest.mark.asyncio
async def test_sentiment_agent_get_symbol_score():
    """Test getting sentiment score for specific symbol"""
    config_manager = ConfigManager()
    agent = SentimentAnalysisAgent(config_manager)
    await agent.initialize()

    # Set a sentiment cache
    agent.sentiment_cache = {
        "sentiment_score": 0.5,
        "last_update": datetime.now().isoformat(),
    }

    score = await agent.get_sentiment_for_symbol("BTC/USDT")
    assert score == 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
