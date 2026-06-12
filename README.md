# Binance Futures Testnet Trading Bot (USDT-M)

A production-quality Python CLI application to place orders on the Binance Futures Testnet (USDT-M). This project uses standard Python libraries, featuring clean separation of concerns, strict parameter validation, local server time synchronization, and robust error mapping.

---

## Architecture Overview

The codebase follows **Clean Architecture** patterns, separating parsing, validation, business logic, configuration, and API communication:

```
trading_bot/
│
├── bot/
│   ├── __init__.py
│   ├── client.py          # Handles REST sessions, HMAC-SHA256 signatures, server time sync, and exception mapping
│   ├── orders.py          # Routes order parameters to Standard (/order) or Algo (/algoOrder) endpoints
│   ├── validators.py      # Validates types, quantity constraints, and trigger parameters
│   ├── logging_config.py  # Standard Logger config writing to logs/trading_bot.log
│   └── exceptions.py      # Custom Exceptions hierarchy (AuthenticationError, InsufficientBalanceError, etc.)
│
├── cli.py                 # CLI entrypoint; parses inputs and outputs premium status logs
├── config.py              # Loads .env configuration and handles validation of credentials
├── mock_runner.py         # Mock runner to dry-run/test bot outputs without real API credentials
├── requirements.txt       # Pinpoint package dependencies
├── .env.example           # Reference environmental keys
└── README.md              # Documentation and usage guide
```

### Core Design Decisions
1. **Direct REST Integration**: Handcrafted signing using `hmac` and `hashlib` over `requests` yields minimal, robust dependencies and simplifies error tracing.
2. **Server Time Synchronization**: The client requests `/fapi/v1/time` to calculate latency-adjusted local-to-server time offsets. This completely prevents the notorious `-1021 INVALID_TIMESTAMP` Binance error.
3. **Algo Order Endpoint for STOP-LIMIT**: Standard STOP/STOP_LIMIT orders have been migrated by Binance to the Algo Order API (`/fapi/v1/algoOrder`). The bot automatically detects `STOP_LIMIT` orders and targets the correct endpoint with proper parameters (`type="STOP"`, `algoType="CONDITIONAL"`, `triggerPrice=stop_price`).

---

## Installation & Setup

### Prerequisites
- Python 3.10 or higher (Tested on Python 3.14.0)

### 1. Clone the Project & Create Virtual Environment
```powershell
# Navigate to the project root
cd "c:\Project\Trading Bot"

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Windows (CMD):
.venv\Scripts\activate.bat
# On Linux/macOS:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup Credentials
Copy the `.env.example` file to `.env` and fill in your Binance Futures Testnet credentials:
```bash
cp .env.example .env
```
Open `.env` and configure:
```env
BINANCE_API_KEY=your_actual_testnet_api_key
BINANCE_API_SECRET=your_actual_testnet_api_secret
BINANCE_BASE_URL=https://testnet.binancefuture.com
RECV_WINDOW=5000
```

---

## Usage Examples

The CLI takes arguments for `--symbol`, `--side`, `--type`, `--quantity`, `--price`, and `--stop-price`.

### Placing a Market Order (BUY)
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### Placing a Limit Order (SELL)
```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 62500
```

### Placing a Stop-Limit Order (BUY - Bonus Feature)
```bash
python cli.py --symbol BTCUSDT --side BUY --type STOP_LIMIT --quantity 0.001 --price 63000 --stop-price 62800
```

---

## Dry-Run Testing with `mock_runner.py`

To verify the bot without real API keys, use the provided `mock_runner.py` script. It simulates all REST responses and maps parameters exactly like the live Binance client.

### Simulated Success (LIMIT Order)
```bash
python mock_runner.py --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001 --price 50000
```
**Output:**
```
=== ORDER REQUEST ===
Symbol: BTCUSDT
Side: BUY
Type: LIMIT
Quantity: 0.001
Price: 50000.0

=== ORDER RESPONSE ===
Order ID: 123456
Status: NEW
Executed Quantity: 0.001
Average Price: 50000

✓ Order placed successfully
```

### Simulated Success (STOP_LIMIT Order)
```bash
python mock_runner.py --symbol BTCUSDT --side BUY --type STOP_LIMIT --quantity 0.001 --price 50000 --stop-price 49500
```
**Output:**
```
=== ORDER REQUEST ===
Symbol: BTCUSDT
Side: BUY
Type: STOP_LIMIT
Quantity: 0.001
Price: 50000.0
Stop Price: 49500.0

=== ORDER RESPONSE ===
Order ID: algo-order-9876543-uuid
Status: NEW
Executed Quantity: 0
Average Price: 0

✓ Order placed successfully
```

### Simulated Failure (Insufficient Balance)
```bash
python mock_runner.py --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001 --price 50000 --mock-fail --fail-type balance
```
**Output:**
```
=== ORDER REQUEST ===
Symbol: BTCUSDT
Side: BUY
Type: LIMIT
Quantity: 0.001
Price: 50000.0

=== ORDER RESPONSE ===
Error: Insufficient funds: Margin is insufficient.

✗ Order failed
```

### Simulated Failure (Authentication Error)
```bash
python mock_runner.py --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001 --price 50000 --mock-fail --fail-type auth
```
**Output:**
```
=== ORDER REQUEST ===
Symbol: BTCUSDT
Side: BUY
Type: LIMIT
Quantity: 0.001
Price: 50000.0

=== ORDER RESPONSE ===
Error: Authentication failed (Binance code -2015): Invalid API-key, IP, or permissions for action.

✗ Order failed
```

---

## Log Output (`logs/trading_bot.log`)

The bot writes formatted traces of requests, raw responses, and exception stack-traces to `logs/trading_bot.log`. Example logs:

```
2026-06-12 10:50:04 INFO CLI Input parameters - Symbol: BTCUSDT, Side: BUY, Type: LIMIT, Quantity: 0.001, Price: 50000.0, Stop Price: None
2026-06-12 10:50:04 INFO Order Request Details - Symbol: BTCUSDT, Side: BUY, Type: LIMIT, Quantity: 0.001, Price: 50000.0, Stop Price: None
2026-06-12 10:50:04 INFO Synchronized with Binance server time. Offset: -0.66 ms
2026-06-12 10:50:04 INFO Sending Request: POST /fapi/v1/order Params: {'symbol': 'BTCUSDT', 'side': 'BUY', 'type': 'LIMIT', 'quantity': '0.001', 'price': '50000.0', 'timeInForce': 'GTC', 'timestamp': 1781241604892, 'recvWindow': 10000}
2026-06-12 10:50:04 INFO Received Response: {'orderId': 123456, 'symbol': 'BTCUSDT', 'pair': 'BTCUSDT', 'status': 'NEW', 'clientOrderId': 'mock_client_order_id_abc', 'price': '50000.0', 'avgPrice': '50000.0', 'origQty': '0.001', 'executedQty': '0.001', 'cumQty': '0.001', 'cumQuote': '50.0', 'timeInForce': 'GTC', 'type': 'LIMIT', 'side': 'BUY', 'positionSide': 'BOTH', 'stopPrice': '0', 'workingType': 'CONTRACT_PRICE', 'origType': 'LIMIT', 'time': 1781241604894, 'updateTime': 1781241604894}
2026-06-12 10:50:04 INFO Order Response Details - Order ID: 123456, Status: NEW, Executed Qty: 0.001, Avg Price: 50000.0
2026-06-12 10:50:13 ERROR Binance API Error Response - Status Code: 400, Code: -2019, Msg: Margin is insufficient.
2026-06-12 10:50:13 ERROR Trading Bot Exception: Insufficient funds: Margin is insufficient.
```

---

## Running Automated Tests
The validation suite can be executed using `pytest` inside the virtual environment:
```bash
python -m pytest
```
**Results Output:**
```
collected 11 items
tests\test_validators.py ...........                                     [100%]
============================= 11 passed in 0.02s ==============================
```
