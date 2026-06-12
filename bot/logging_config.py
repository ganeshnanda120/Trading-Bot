"""
Logging configuration for the Binance Futures Trading Bot.
Sets up file logging in the `logs/` directory.
"""

import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """
    Configures the application logger.
    Creates a 'logs' directory if it doesn't exist.
    Logs are written to 'logs/trading_bot.log'.
    """
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_file = os.path.join(log_dir, "trading_bot.log")
    
    # Define formatting: 2025-01-01 10:00:00 INFO message
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Create file handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates
    if root_logger.handlers:
        root_logger.handlers.clear()
        
    root_logger.addHandler(file_handler)
    
    # Return the configured logger
    return logging.getLogger("trading_bot")
