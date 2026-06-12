"""
Input validation for order parameters.
"""

from typing import Optional
from bot.exceptions import ValidationError

def validate_order_params(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None
) -> None:
    """
    Validates the CLI parameters for placing an order.
    Raises ValidationError if any check fails.
    """
    # 1. Validate Symbol
    if not symbol or not isinstance(symbol, str) or not symbol.strip():
        raise ValidationError("Symbol must not be empty.")
    
    # 2. Validate Side
    side_upper = side.upper() if isinstance(side, str) else ""
    if side_upper not in ("BUY", "SELL"):
        raise ValidationError(f"Side must be 'BUY' or 'SELL'. Got: '{side}'")
        
    # 3. Validate Order Type
    type_upper = order_type.upper() if isinstance(order_type, str) else ""
    valid_types = ("MARKET", "LIMIT", "STOP_LIMIT")
    if type_upper not in valid_types:
        raise ValidationError(f"Order Type must be one of {valid_types}. Got: '{order_type}'")
        
    # 4. Validate Quantity
    try:
        qty_val = float(quantity)
    except (ValueError, TypeError):
        raise ValidationError(f"Quantity must be a valid number. Got: '{quantity}'")
        
    if qty_val <= 0:
        raise ValidationError(f"Quantity must be greater than 0. Got: {qty_val}")
        
    # 5. Validate Price for LIMIT or STOP_LIMIT
    if type_upper in ("LIMIT", "STOP_LIMIT"):
        if price is None:
            raise ValidationError(f"Price is required for {type_upper} orders.")
        try:
            price_val = float(price)
        except (ValueError, TypeError):
            raise ValidationError(f"Price must be a valid number. Got: '{price}'")
        if price_val <= 0:
            raise ValidationError(f"Price must be greater than 0. Got: {price_val}")
            
    # 6. Validate Stop Price for STOP_LIMIT
    if type_upper == "STOP_LIMIT":
        if stop_price is None:
            raise ValidationError("Stop price is required for STOP_LIMIT orders.")
        try:
            stop_val = float(stop_price)
        except (ValueError, TypeError):
            raise ValidationError(f"Stop price must be a valid number. Got: '{stop_price}'")
        if stop_val <= 0:
            raise ValidationError(f"Stop price must be greater than 0. Got: {stop_val}")
