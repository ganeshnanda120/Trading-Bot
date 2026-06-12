"""
Binance Futures Testnet API Client.
Handles connection, signing, request formatting, and custom error mapping.
"""

import hmac
import hashlib
import time
import urllib.parse
import requests
import logging
from typing import Dict, Any, Optional

from bot.exceptions import (
    AuthenticationError,
    InsufficientBalanceError,
    InvalidSymbolError,
    NetworkError,
    BinanceAPIError,
)

logger = logging.getLogger("trading_bot")

class BinanceClient:
    """
    Custom client to communicate with Binance Futures Testnet REST API.
    """
    def __init__(self, api_key: str, api_secret: str, base_url: str, recv_window: int = 5000):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip('/')
        self.recv_window = recv_window
        self.time_offset = 0.0
        
        # Initialize connection session
        self.session = requests.Session()
        self.session.headers.update({
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded"
        })

    def sync_server_time(self) -> float:
        """
        Synchronizes client time with Binance server time.
        Calculates time offset to prevent INVALID_TIMESTAMP (-1021) errors.
        """
        url = f"{self.base_url}/fapi/v1/time"
        try:
            start_time = time.time()
            response = self.session.get(url, timeout=10)
            end_time = time.time()
            
            response.raise_for_status()
            server_time = response.json()["serverTime"]
            
            # Estimate latency (rtt / 2)
            rtt = (end_time - start_time) * 1000
            estimated_local_time = (start_time * 1000) + (rtt / 2)
            
            self.time_offset = server_time - estimated_local_time
            logger.info(f"Synchronized with Binance server time. Offset: {self.time_offset:.2f} ms")
            return self.time_offset
        except requests.exceptions.Timeout as e:
            logger.warning("Timeout while synchronizing server time. Using 0 offset.")
            raise NetworkError("Timeout syncing server time.") from e
        except Exception as e:
            logger.warning(f"Failed to synchronize server time: {e}. Using 0 offset.")
            # Do not raise, fallback to local clock but log it
            self.time_offset = 0.0
            return 0.0

    def _get_timestamp_ms(self) -> int:
        """Returns signed timestamp in milliseconds including synchronized offset."""
        return int(time.time() * 1000 + self.time_offset)

    def _sign_payload(self, params: Dict[str, Any]) -> str:
        """
        Generates HMAC-SHA256 signature for the given parameters dictionary.
        """
        # Ensure parameters are sorted/formatted
        query_string = urllib.parse.urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _handle_response_error(self, response: requests.Response) -> None:
        """
        Parses response status and details, raising appropriate custom exceptions.
        """
        try:
            error_data = response.json()
            code = error_data.get("code", 0)
            msg = error_data.get("msg", "Unknown error")
        except ValueError:
            # Not JSON
            code = 0
            msg = response.text or "Unknown response structure"
            
        logger.error(f"Binance API Error Response - Status Code: {response.status_code}, Code: {code}, Msg: {msg}")
        
        # Map specific codes to custom exceptions
        # -1002: Unauthorized, -2015: Invalid API Key, -1022: Invalid Signature
        if code in (-1002, -1022, -2015):
            raise AuthenticationError(f"Authentication failed (Binance code {code}): {msg}")
        
        # -1121: Invalid symbol
        elif code == -1121:
            raise InvalidSymbolError(f"Invalid symbol: {msg}")
            
        # -2019: Insufficient margin, -2027: Insufficient balance
        elif code in (-2019, -2027):
            raise InsufficientBalanceError(f"Insufficient funds: {msg}")
            
        # Fallback to general API exception
        else:
            raise BinanceAPIError(code=code, message=msg, status_code=response.status_code)

    def request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None, signed: bool = True) -> Dict[str, Any]:
        """
        Sends requests to the Binance Futures API.
        Automatically signs payload if signed is True.
        """
        if params is None:
            params = {}
            
        # If credentials are not set when calling a signed endpoint
        if signed and (not self.api_key or not self.api_secret):
            raise AuthenticationError("API Key and Secret must be configured in .env for signed requests.")

        if signed:
            # Inject security parameters
            params["timestamp"] = self._get_timestamp_ms()
            params["recvWindow"] = self.recv_window
            
            # Generate signature and append
            signature = self._sign_payload(params)
            params["signature"] = signature

        url = f"{self.base_url}{endpoint}"
        
        # Log request parameters (excluding secret, though signature is fine to log)
        log_params = {k: v for k, v in params.items() if k not in ("signature",)}
        logger.info(f"Sending Request: {method} {endpoint} Params: {log_params}")

        try:
            if method.upper() == "POST":
                # For POST endpoints, parameters can be sent as form data (x-www-form-urlencoded)
                response = self.session.post(url, data=params, timeout=15)
            elif method.upper() == "GET":
                response = self.session.get(url, params=params, timeout=15)
            else:
                response = self.session.request(method, url, params=params, timeout=15)
                
            if response.status_code != 200:
                self._handle_response_error(response)
                
            response_json = response.json()
            logger.info(f"Received Response: {response_json}")
            return response_json
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Network timeout contacting Binance API: {e}")
            raise NetworkError("Connection timed out. Please verify your connection.") from e
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Network connection failure: {e}")
            raise NetworkError("Connection failed. Check your internet connection and base URL.") from e
        except requests.exceptions.RequestException as e:
            # Don't mask custom exceptions raised inside _handle_response_error
            if isinstance(e, requests.exceptions.HTTPError) and response.status_code != 200:
                # Handled by _handle_response_error already, but if it fell through
                self._handle_response_error(response)
            logger.error(f"Unexpected network request exception: {e}")
            raise NetworkError(f"Network request failure: {e}") from e
