"""
Mock runner for testing the Binance Futures Trading Bot CLI.
Simulates Binance API responses without requiring real API keys.
"""

import sys
import os
import time
from unittest.mock import patch, MagicMock

# Set mock credentials so Config.validate() succeeds
os.environ["BINANCE_API_KEY"] = "MOCK_BINANCE_API_KEY_12345"
os.environ["BINANCE_API_SECRET"] = "MOCK_BINANCE_API_SECRET_67890"
os.environ["BINANCE_BASE_URL"] = "https://testnet.binancefuture.com"

# Import mock utility
import requests

def mock_request(method, url, **kwargs):
    """
    Simulates Binance REST responses.
    """
    mock_response = MagicMock(spec=requests.Response)
    
    # Extract endpoint from URL
    url_lower = url.lower()
    
    # 1. Mock GET /fapi/v1/time
    if "/fapi/v1/time" in url_lower:
        mock_response.status_code = 200
        mock_response.json.return_value = {"serverTime": int(time.time() * 1000)}
        return mock_response
        
    # Check if we should simulate failure
    simulate_fail = os.getenv("MOCK_SIMULATE_FAIL", "false").lower() == "true"
    fail_type = os.getenv("MOCK_FAIL_TYPE", "balance")  # balance, auth, symbol, timeout
    
    if simulate_fail:
        if fail_type == "balance":
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "code": -2019,
                "msg": "Margin is insufficient."
            }
        elif fail_type == "auth":
            mock_response.status_code = 401
            mock_response.json.return_value = {
                "code": -2015,
                "msg": "Invalid API-key, IP, or permissions for action."
            }
        elif fail_type == "symbol":
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "code": -1121,
                "msg": "Invalid symbol."
            }
        elif fail_type == "timeout":
            raise requests.exceptions.Timeout("Simulated network timeout connection.")
        else:
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_response.json.side_effect = ValueError("Not JSON")
            
        return mock_response

    # 2. Mock POST /fapi/v1/algoOrder
    if "/fapi/v1/algoorder" in url_lower:
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "algo-order-9876543-uuid",
            "status": 200,
            "msg": "Success"
        }
        return mock_response

    # 3. Mock POST /fapi/v1/order
    if "/fapi/v1/order" in url_lower:
        # Check params from kwargs['data'] (sent via post)
        post_data = kwargs.get("data", {})
        symbol = post_data.get("symbol", "BTCUSDT")
        side = post_data.get("side", "BUY")
        order_type = post_data.get("type", "LIMIT")
        qty = post_data.get("quantity", "0.001")
        price = post_data.get("price", "0.00")
        
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "orderId": 123456,
            "symbol": symbol,
            "pair": symbol,
            "status": "NEW",
            "clientOrderId": "mock_client_order_id_abc",
            "price": str(price),
            "avgPrice": str(price) if order_type == "LIMIT" else "50000.00",
            "origQty": str(qty),
            "executedQty": str(qty),
            "cumQty": str(qty),
            "cumQuote": "50.0",
            "timeInForce": "GTC",
            "type": order_type,
            "side": side,
            "positionSide": "BOTH",
            "stopPrice": "0",
            "workingType": "CONTRACT_PRICE",
            "origType": order_type,
            "time": int(time.time() * 1000),
            "updateTime": int(time.time() * 1000)
        }
        return mock_response

    # Default fallback
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    return mock_response

def run_cli_with_mocks():
    """
    Intercepts network requests inside requests.Session using unittest.mock.patch.
    """
    # Intercept session requests
    with patch("requests.Session.request", side_effect=mock_request):
        # Now run the actual bot cli main
        from cli import main as cli_main
        cli_main()

if __name__ == "__main__":
    # Check if user requested mock failure
    # We will strip --mock-fail and options from sys.argv before running argparse
    simulate_fail = False
    fail_type = "balance"
    
    if "--mock-fail" in sys.argv:
        simulate_fail = True
        idx = sys.argv.index("--mock-fail")
        sys.argv.pop(idx)
        
        if "--fail-type" in sys.argv:
            f_idx = sys.argv.index("--fail-type")
            if f_idx + 1 < len(sys.argv):
                fail_type = sys.argv[f_idx + 1]
                sys.argv.pop(f_idx + 1)
            sys.argv.pop(f_idx)
            
    os.environ["MOCK_SIMULATE_FAIL"] = "true" if simulate_fail else "false"
    os.environ["MOCK_FAIL_TYPE"] = fail_type
    
    # Run the bot CLI
    run_cli_with_mocks()
