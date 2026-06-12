"""
Configuration loader for the trading bot.
Loads values from environment variables or a .env file.
"""

import os
from dotenv import load_dotenv
from bot.exceptions import AuthenticationError

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """
    Exposes configuration variables.
    """
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "").strip()
    BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "").strip()
    BINANCE_BASE_URL = os.getenv("BINANCE_BASE_URL", "https://testnet.binancefuture.com").strip()
    
    try:
        RECV_WINDOW = int(os.getenv("RECV_WINDOW", "5000").strip())
    except ValueError:
        RECV_WINDOW = 5000

    @classmethod
    def validate(cls) -> None:
        """
        Validates that necessary API credentials are present.
        """
        if not cls.BINANCE_API_KEY or not cls.BINANCE_API_SECRET:
            raise AuthenticationError(
                "BINANCE_API_KEY or BINANCE_API_SECRET is not configured. "
                "Please copy .env.example to .env and fill in your credentials."
            )
