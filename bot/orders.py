"""
Order execution module.
Handles routing order details to standard or algo endpoints.
"""

from typing import Dict, Any, Optional
from bot.client import BinanceClient

def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None
) -> Dict[str, Any]:
    """
    Routes and executes an order on Binance Futures Testnet.
    
    Returns a normalized response dictionary:
        {
            "order_id": str/int,
            "status": str,
            "executed_qty": float,
            "avg_price": float
        }
    """
    symbol = symbol.upper()
    side = side.upper()
    order_type = order_type.upper()
    
    if order_type == "STOP_LIMIT":
        # Target the Algo Order API
        endpoint = "/fapi/v1/algoOrder"
        params = {
            "symbol": symbol,
            "side": side,
            "type": "STOP",
            "algoType": "CONDITIONAL",
            "quantity": str(quantity),
            "price": str(price),
            "triggerPrice": str(stop_price),
        }
        
        response = client.request("POST", endpoint, params=params, signed=True)
        
        # Normalize response for STOP_LIMIT algo order
        # Response typically has: {"id": "uuid", "status": 200, "msg": "Success"}
        order_id = response.get("id", "N/A")
        status = "NEW" if response.get("status") == 200 or response.get("msg") == "Success" else "REJECTED"
        
        return {
            "order_id": order_id,
            "status": status,
            "executed_qty": 0.0,
            "avg_price": 0.0,
            "raw": response
        }
    else:
        # Target the standard Order API
        endpoint = "/fapi/v1/order"
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": str(quantity),
        }
        
        if order_type == "LIMIT":
            params["price"] = str(price)
            # LIMIT orders require timeInForce. GTC is the standard choice.
            params["timeInForce"] = "GTC"
            
        response = client.request("POST", endpoint, params=params, signed=True)
        
        # Normalize response for standard orders
        order_id = response.get("orderId", "N/A")
        status = response.get("status", "UNKNOWN")
        
        # Parse quantities and prices safely
        try:
            executed_qty = float(response.get("executedQty", 0.0))
        except (ValueError, TypeError):
            executed_qty = 0.0
            
        try:
            avg_price = float(response.get("avgPrice", 0.0))
        except (ValueError, TypeError):
            avg_price = 0.0
            
        # Fallback to limit price if avg_price is 0 for displaying
        if avg_price == 0.0 and price is not None:
            avg_price = float(price)
            
        return {
            "order_id": order_id,
            "status": status,
            "executed_qty": executed_qty,
            "avg_price": avg_price,
            "raw": response
        }
