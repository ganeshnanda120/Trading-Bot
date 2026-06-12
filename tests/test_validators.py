import pytest
from bot.validators import validate_order_params
from bot.exceptions import ValidationError

def test_valid_market_order():
    # Should not raise any exceptions
    validate_order_params("BTCUSDT", "BUY", "MARKET", 0.001)
    validate_order_params("ETHUSDT", "SELL", "MARKET", 1.5)

def test_valid_limit_order():
    validate_order_params("BTCUSDT", "BUY", "LIMIT", 0.001, price=50000.0)
    validate_order_params("ETHUSDT", "SELL", "LIMIT", 1.5, price=3000.5)

def test_valid_stop_limit_order():
    validate_order_params("BTCUSDT", "BUY", "STOP_LIMIT", 0.001, price=50000.0, stop_price=49500.0)

def test_invalid_symbol():
    with pytest.raises(ValidationError, match="Symbol must not be empty"):
        validate_order_params("", "BUY", "MARKET", 0.001)
    with pytest.raises(ValidationError, match="Symbol must not be empty"):
        validate_order_params("   ", "BUY", "MARKET", 0.001)

def test_invalid_side():
    with pytest.raises(ValidationError, match="Side must be 'BUY' or 'SELL'"):
        validate_order_params("BTCUSDT", "HOLD", "MARKET", 0.001)

def test_invalid_order_type():
    with pytest.raises(ValidationError, match="Order Type must be one of"):
        validate_order_params("BTCUSDT", "BUY", "TRAILING_STOP", 0.001)

def test_invalid_quantity():
    with pytest.raises(ValidationError, match="Quantity must be greater than 0"):
        validate_order_params("BTCUSDT", "BUY", "MARKET", 0.0)
    with pytest.raises(ValidationError, match="Quantity must be greater than 0"):
        validate_order_params("BTCUSDT", "BUY", "MARKET", -1.0)
    with pytest.raises(ValidationError, match="Quantity must be a valid number"):
        validate_order_params("BTCUSDT", "BUY", "MARKET", "invalid")

def test_missing_price_for_limit():
    with pytest.raises(ValidationError, match="Price is required for LIMIT orders"):
        validate_order_params("BTCUSDT", "BUY", "LIMIT", 0.001)

def test_invalid_price_for_limit():
    with pytest.raises(ValidationError, match="Price must be greater than 0"):
        validate_order_params("BTCUSDT", "BUY", "LIMIT", 0.001, price=0)
    with pytest.raises(ValidationError, match="Price must be greater than 0"):
        validate_order_params("BTCUSDT", "BUY", "LIMIT", 0.001, price=-10.0)

def test_missing_stop_price_for_stop_limit():
    with pytest.raises(ValidationError, match="Stop price is required for STOP_LIMIT orders"):
        validate_order_params("BTCUSDT", "BUY", "STOP_LIMIT", 0.001, price=50000.0)

def test_invalid_stop_price_for_stop_limit():
    with pytest.raises(ValidationError, match="Stop price must be greater than 0"):
        validate_order_params("BTCUSDT", "BUY", "STOP_LIMIT", 0.001, price=50000.0, stop_price=0.0)
