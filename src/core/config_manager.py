"""
VOLT Trading Configuration Manager
Handles all configuration settings
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import configparser


class ConfigManager:
    """Central configuration management for VOLT Trading"""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        # Only create if it's actually a directory path, not a file
        if not self.config_dir.suffix:  # No file extension
            self.config_dir.mkdir(exist_ok=True)
        else:  # It's a file path
            self.config_dir = self.config_dir.parent
        self.config = {}
        self.load_default_config()
        self.load_config()

    def load_default_config(self):
        """Load default configuration"""
        self.config = {
            "trading": {
                "initial_capital": 20000,
                "max_position_size": 0.10,
                "risk_per_trade": 0.025,
                "stop_loss": 0.05,
                "take_profit": 0.10,
                "max_drawdown": 0.15,
                "timeframe": "5m",
                "pairs": ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "AVAX/USDT"],
            },
            "exchange": {
                "name": "binance",
                "sandbox": True,
                "api_key": "",
                "api_secret": "",
                "password": "",
            },
            "risk_management": {
                "kelly_criterion": True,
                "max_leverage": 1.0,
                "correlation_limit": 0.7,
                "volatility_adjustment": True,
            },
            "ml_models": {
                "lstm_enabled": True,
                "reinforcement_learning": True,
                "sentiment_analysis": True,
                "anomaly_detection": True,
            },
            "anonymity": {
                "tor_enabled": True,
                "vpn_enabled": True,
                "proxy_rotation": True,
            },
            "monitoring": {
                "dashboard_port": 8501,
                "log_level": "INFO",
                "metrics_enabled": True,
            },
        }

    def load_config(self, config_file: str = "trading.json") -> bool:
        """Load configuration from file"""
        config_path = self.config_dir / config_file

        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    file_config = json.load(f)
                    self._merge_config(self.config, file_config)
                return True
            except Exception as e:
                print(f"Error loading config: {e}")
                return False
        return False

    def save_config(self, config_file: str = "trading.json"):
        """Save current configuration to file"""
        config_path = self.config_dir / config_file

        try:
            with open(config_path, "w") as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (dot notation supported)"""
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """Set configuration value by key (dot notation supported)"""
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def get_trading_config(self) -> Dict[str, Any]:
        """Get trading configuration"""
        return self.get("trading", {})

    def get_exchange_config(self) -> Dict[str, Any]:
        """Get exchange configuration"""
        return self.get("exchange", {})

    def get_risk_config(self) -> Dict[str, Any]:
        """Get risk management configuration"""
        return self.get("risk_management", {})

    def get_ml_config(self) -> Dict[str, Any]:
        """Get machine learning configuration"""
        return self.get("ml_models", {})

    def get_anonymity_config(self) -> Dict[str, Any]:
        """Get anonymity configuration"""
        return self.get("anonymity", {})

    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration"""
        return self.get("monitoring", {})

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            "level": self.get("monitoring.log_level", "INFO"),
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": "logs/volt_trading.log",
        }

    def _merge_config(self, base: Dict, override: Dict):
        """Recursively merge configuration dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value


if __name__ == "__main__":
    # Test configuration manager
    config = ConfigManager()
    config.save_config()
    print("✅ Configuration manager test completed")
