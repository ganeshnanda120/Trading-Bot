"""
Custom exceptions for the Binance Futures Trading Bot.
"""

class TradingBotError(Exception):
    """Base exception for all trading bot related errors."""
    pass

class ValidationError(TradingBotError):
    """Raised when command-line parameters or config values fail validation."""
    pass

class AuthenticationError(TradingBotError):
    """Raised when there are authentication issues (e.g. invalid API key or signature)."""
    pass

class InsufficientBalanceError(TradingBotError):
    """Raised when there is insufficient balance or margin to place an order."""
    pass

class InvalidSymbolError(TradingBotError):
    """Raised when the requested symbol is invalid or not found on the exchange."""
    pass

class NetworkError(TradingBotError):
    """Raised on connection failures, DNS failures, or HTTP request timeouts."""
    pass

class BinanceAPIError(TradingBotError):
    """
    General exception raised when the Binance API returns an error response.
    
    Attributes:
        code (int): The error code returned by Binance (e.g. -1013).
        message (str): The error message returned by Binance.
        status_code (int): The HTTP status code of the response.
    """
    def __init__(self, code: int, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(f"Binance API Error {code}: {message} (HTTP {status_code})")
