"""
VOLT Trading Logger Setup
Centralized logging configuration
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Dict, Any


def setup_logging(config: Dict[str, Any]):
    """Setup logging configuration"""

    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Extract configuration
    level = config.get("level", "INFO")
    format_str = config.get(
        "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    log_file = config.get("file", "logs/volt_trading.log")

    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Create formatters
    formatter = logging.Formatter(format_str)

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Set specific logger levels
    logging.getLogger("src").setLevel(numeric_level)
    logging.getLogger("agents").setLevel(numeric_level)
    logging.getLogger("core").setLevel(numeric_level)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)


if __name__ == "__main__":
    # Test logging setup
    config = {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": "logs/test.log",
    }

    setup_logging(config)

    logger = get_logger("test")
    logger.info("✅ Logging setup test completed")
