"""
Command Line Interface (CLI) for the Binance Futures Trading Bot.
"""

import sys
import argparse
import logging
from typing import Optional

# Configure console encoding to support unicode characters like checkmarks and cross marks
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from config import Config
from bot.logging_config import setup_logging
from bot.exceptions import TradingBotError, ValidationError, BinanceAPIError
from bot.validators import validate_order_params
from bot.client import BinanceClient
from bot.orders import place_order

def main():
    # 1. Initialize logging
    logger = setup_logging()
    
    # 2. Parse command line arguments
    parser = argparse.ArgumentParser(description="Binance Futures Testnet (USDT-M) Trading Bot CLI")
    parser.add_argument("--symbol", type=str, required=True, help="Trading symbol (e.g. BTCUSDT)")
    parser.add_argument("--side", type=str, required=True, help="Order side (BUY or SELL)")
    parser.add_argument("--type", type=str, required=True, help="Order type (MARKET, LIMIT, or STOP_LIMIT)")
    parser.add_argument("--quantity", type=float, required=True, help="Quantity to trade")
    parser.add_argument("--price", type=float, default=None, help="Limit price (required for LIMIT & STOP_LIMIT)")
    parser.add_argument("--stop-price", type=float, default=None, help="Stop trigger price (required for STOP_LIMIT)")
    
    args = parser.parse_args()
    
    # Log the parsed CLI inputs
    logger.info(f"CLI Input parameters - Symbol: {args.symbol}, Side: {args.side}, Type: {args.type}, Quantity: {args.quantity}, Price: {args.price}, Stop Price: {args.stop_price}")

    # 3. Validate input parameters
    try:
        validate_order_params(
            symbol=args.symbol,
            side=args.side,
            order_type=args.type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price
        )
    except ValidationError as e:
        logger.error(f"Validation Error: {e}")
        print(f"\n✗ Order failed due to validation error:")
        print(f"  {e}")
        sys.exit(1)

    # 4. Load config and validate credentials
    try:
        Config.validate()
    except TradingBotError as e:
        logger.error(f"Configuration/Authentication Error: {e}")
        print(f"\n✗ Order failed")
        print(f"  Error: {e}")
        sys.exit(1)

    # 5. Display Order Request Preview
    print("\n=== ORDER REQUEST ===")
    print(f"Symbol: {args.symbol.upper()}")
    print(f"Side: {args.side.upper()}")
    print(f"Type: {args.type.upper()}")
    print(f"Quantity: {args.quantity}")
    if args.price is not None:
        print(f"Price: {args.price}")
    if args.stop_price is not None:
        print(f"Stop Price: {args.stop_price}")
    print()

    # Log request details
    logger.info(
        f"Order Request Details - Symbol: {args.symbol.upper()}, Side: {args.side.upper()}, "
        f"Type: {args.type.upper()}, Quantity: {args.quantity}, "
        f"Price: {args.price}, Stop Price: {args.stop_price}"
    )

    # 6. Initialize Client & Sync Time
    client = BinanceClient(
        api_key=Config.BINANCE_API_KEY,
        api_secret=Config.BINANCE_API_SECRET,
        base_url=Config.BINANCE_BASE_URL,
        recv_window=Config.RECV_WINDOW
    )
    
    try:
        # Sync server time to prevent timestamp errors
        client.sync_server_time()
    except TradingBotError as e:
        # Log network synchronization issue, but we can continue and let the endpoint try
        logger.warning(f"Could not synchronize server time: {e}. Attempting placement anyway.")

    # 7. Execute Order
    try:
        result = place_order(
            client=client,
            symbol=args.symbol,
            side=args.side,
            order_type=args.type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price
        )
        
        # Display successful order details
        print("=== ORDER RESPONSE ===")
        print(f"Order ID: {result['order_id']}")
        print(f"Status: {result['status']}")
        
        # Safe float display formatting
        if result['executed_qty'] == int(result['executed_qty']):
            print(f"Executed Quantity: {int(result['executed_qty'])}")
        else:
            print(f"Executed Quantity: {result['executed_qty']}")
            
        if result['avg_price'] == int(result['avg_price']):
            print(f"Average Price: {int(result['avg_price'])}")
        else:
            print(f"Average Price: {result['avg_price']}")
        print()
        
        # Log successful response
        logger.info(
            f"Order Response Details - Order ID: {result['order_id']}, Status: {result['status']}, "
            f"Executed Qty: {result['executed_qty']}, Avg Price: {result['avg_price']}"
        )
        print("✓ Order placed successfully")
        sys.exit(0)

    except BinanceAPIError as e:
        logger.error(f"Binance API Error: {e}")
        print("=== ORDER RESPONSE ===")
        print(f"Error Code: {e.code}")
        print(f"Error Message: {e.message}")
        print()
        print("✗ Order failed")
        sys.exit(1)
        
    except TradingBotError as e:
        # Handles InsufficientBalanceError, AuthenticationError, InvalidSymbolError, NetworkError, etc.
        logger.error(f"Trading Bot Exception: {e}")
        print("=== ORDER RESPONSE ===")
        print(f"Error: {e}")
        print()
        print("✗ Order failed")
        sys.exit(1)
        
    except Exception as e:
        logger.exception(f"Unexpected error executing order: {e}")
        print("=== ORDER RESPONSE ===")
        print(f"Unexpected Error: {e}")
        print()
        print("✗ Order failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
