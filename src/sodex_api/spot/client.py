"""Spot trading client for Sodex API."""

import requests
import time
import hashlib
import hmac
import uuid
import json
from typing import Dict, List, Optional, Any
from loguru import logger

from ..core import BaseClient
from ..config import Config
from ..models import Balance, Orderbook, OBItem, Order, KlineData, TickerData, TradeData, OrderFill, SymbolInfo, OrderSide
from ..exceptions import SodexAPIError

# Constants
DEFAULT_ORDERBOOK_LIMIT = 100
REQUEST_TIMEOUT = 10.0
MAX_PAGE_SIZE = 100

# Symbol mappings for Sodex API
SYMBOL_MAPPING = {
    "BTCUSDT": "BTC_USDT",
    "ETHUSDT": "ETH_USDT", 
    "SOLUSDT": "SOL_USDT"
}

REVERSE_SYMBOL_MAPPING = {v: k for k, v in SYMBOL_MAPPING.items()}


class SpotClient:
    """Client for interacting with Sodex Spot Exchange API."""
    
    def __init__(self):
        self.api_key = Config.SODEX_API_KEY
        self.secret_key = Config.SODEX_SECRET_KEY
        self.base_url = Config.SODEX_BASE_URL
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create and configure requests session."""
        session = requests.Session()
        session.headers.update({
            'X-Access-Key': self.api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'SodexTradingBot/2.0'
        })
        return session

    def _convert_symbol(self, symbol: str, reverse: bool = False) -> str:
        """
        Convert symbol between standard format and Sodex format.
        
        Args:
            symbol: Symbol to convert
            reverse: If True, convert from Sodex format to standard format
            
        Returns:
            Converted symbol
        """
        if not reverse:
            return SYMBOL_MAPPING.get(symbol, symbol)
        else:
            return REVERSE_SYMBOL_MAPPING.get(symbol, symbol)
    
    def _generate_signature(self, sorted_params: Dict[str, str], timestamp: str) -> str:
        """
        Generate HMAC-SHA256 signature for authenticated requests.
        
        Args:
            sorted_params: Sorted request parameters
            timestamp: Request timestamp
            
        Returns:
            Generated signature
            
        Raises:
            SodexAPIError: If signature generation fails
        """
        try:
            # Build raw string from parameters
            raw_string = "&".join([f"{key}={value}" for key, value in sorted_params.items()])
            # Add timestamp parameter
            raw_string += f"&timestamp={timestamp}"
            
            # Generate HMAC-SHA256 signature
            signature = hmac.new(
                self.secret_key.encode('utf-8'),
                raw_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            return signature
        except Exception as e:
            raise SodexAPIError(f"Error generating signature: {str(e)}")
        
    def _handle_response(self, response_data: Dict[str, Any]) -> Any:
        """
        Handle and validate API response.
        
        Args:
            response_data: Raw response data
            
        Returns:
            Response data or None
            
        Raises:
            SodexAPIError: If response indicates error
        """
        if response_data.get('code') != 0:
            error_msg = response_data.get('msg', 'Unknown error')
            raise SodexAPIError(f"API Error: {error_msg}")
        return response_data.get('data')
    
    def _make_request(self, 
                     method: str, 
                     endpoint: str, 
                     params: Optional[Dict[str, Any]] = None, 
                     signed: bool = False) -> Any:
        """
        Make HTTP request to Sodex API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Request parameters
            signed: Whether request requires authentication
            
        Returns:
            Response data
            
        Raises:
            SodexAPIError: If request fails
        """
        if params is None:
            params = {}
        
        timestamp = str(int(time.time() * 1000))
        headers = self.session.headers.copy()
        
        if signed:
            # Add authentication headers
            headers['X-Request-Timestamp'] = timestamp
            headers['X-Request-Nonce'] = str(uuid.uuid4())
            headers['X-Signature'] = self._generate_signature(params, timestamp)
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
            elif method.upper() == 'POST':
                response = requests.post(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            return self._handle_response(response.json())
        
        except requests.exceptions.Timeout:
            raise SodexAPIError(f"Request timeout for {endpoint}")
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error {response.status_code} for {endpoint}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg += f": {error_data.get('msg', 'Unknown error')}"
                except (ValueError, KeyError):
                    error_msg += f": {e.response.text}"
            raise SodexAPIError(error_msg)
        except requests.exceptions.RequestException as e:
            raise SodexAPIError(f"Network error for {endpoint}: {str(e)}")
    
    def get_orderbook(self, symbol: str, limit: int = DEFAULT_ORDERBOOK_LIMIT) -> Orderbook:
        """
        Get orderbook for a trading symbol.
        
        Args:
            symbol: Trading symbol
            limit: Number of price levels to return
            
        Returns:
            Orderbook object
            
        Raises:
            SodexAPIError: If API request fails
            ValueError: If parameters are invalid
        """
        if not symbol or not symbol.strip():
            raise ValueError("Symbol cannot be empty")
        
        if limit <= 0:
            raise ValueError("Limit must be positive")
        
        sodex_symbol = self._convert_symbol(symbol)
        params = {
            'symbol': sodex_symbol,
            'level': limit
        }
        
        try:
            response_data = self._make_request('GET', '/spot/v1/p/quotation/depth', params=params, signed=False)
            return self._format_orderbook(response_data)
        except Exception as e:
            logger.error(f"Failed to get orderbook for {symbol}: {e}")
            raise
    
    def get_account_balances(self) -> List[Balance]:
        """
        Get account balances for all assets.
        
        Returns:
            List of Balance objects
            
        Raises:
            SodexAPIError: If API request fails
        """
        try:
            response_data = self._make_request('GET', '/spot/v1/u/balance/spot', signed=True)
            
            if not isinstance(response_data, list):
                raise SodexAPIError("Invalid balance response format")
            
            balances = []
            for balance_data in response_data:
                try:
                    balance = Balance(
                        symbol=balance_data.get("coin", ""),
                        available=float(balance_data.get("availableBalance", 0)),
                        locked=float(balance_data.get("freeze", 0))
                    )
                    balances.append(balance)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping invalid balance data: {balance_data}, error: {e}")
            
            return balances
        except Exception as e:
            logger.error(f"Failed to get account balances: {e}")
            raise

    def get_account_balance(self, coin: str) -> Optional[Balance]:
        """
        Get account balance for a specific coin.
        
        Args:
            coin: Coin symbol
            
        Returns:
            Balance object or None if not found
            
        Raises:
            SodexAPIError: If API request fails
        """
        if not coin or not coin.strip():
            raise ValueError("Coin cannot be empty")
        
        params = {'coin': coin.strip()}
        
        try:
            response_data = self._make_request('GET', '/spot/v1/u/balance/spot', params=params, signed=True)
            
            if not isinstance(response_data, list) or not response_data:
                return None
            
            balance_data = response_data[0]
            return Balance(
                symbol=balance_data.get("coin", ""),
                available=float(balance_data.get("availableBalance", 0)),
                locked=float(balance_data.get("freeze", 0))
            )
        except Exception as e:
            logger.error(f"Failed to get balance for {coin}: {e}")
            raise
    
    def place_order(self, 
                   symbol: str, 
                   side: OrderSide,
                   order_type: str, 
                   price: float, 
                   quantity: float) -> Optional[str]:
        """
        Place a new order on Sodex.
        
        Args:
            symbol: Trading symbol
            side: Order side ('BUY' or 'SELL') 
            order_type: Order type ('LIMIT', 'MARKET')
            price: Order price
            quantity: Order quantity
            
        Returns:
            Order ID if successful, None otherwise
            
        Raises:
            SodexAPIError: If API request fails
            ValueError: If parameters are invalid
        """
        # Validate parameters
        if not symbol or not symbol.strip():
            raise ValueError("Symbol cannot be empty")
        if side.upper() not in ('BUY', 'SELL'):
            raise ValueError("Side must be 'BUY' or 'SELL'")
        if order_type.upper() not in ('LIMIT', 'MARKET'):
            raise ValueError("Order type must be 'LIMIT' or 'MARKET'")
        if price <= 0:
            raise ValueError("Price must be positive")
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        sodex_symbol = self._convert_symbol(symbol)
        params = {
            'direction': side.upper(),
            'price': f"{price:.2f}",
            'symbol': sodex_symbol,
            'totalAmount': f"{quantity:.4f}",
            'tradeType': order_type.upper(),
        }
        
        logger.debug(f'Placing order: {params}')
        
        try:
            response_data = self._make_request('POST', '/spot/v1/u/trade/order/create', params=params, signed=True)
            return str(response_data) if response_data else None
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise
    
    def cancel_order(self, symbol: str, order_id: str) -> Optional[str]:
        """
        Cancel a specific order.
        
        Args:
            symbol: Trading symbol
            order_id: Order ID to cancel
            
        Returns:
            Cancelled order ID if successful
            
        Raises:
            SodexAPIError: If API request fails
            ValueError: If parameters are invalid
        """
        if not order_id or not order_id.strip():
            raise ValueError("Order ID cannot be empty")
        
        params = {'orderId': order_id.strip()}
        
        try:
            response_data = self._make_request('POST', '/spot/v1/u/trade/order/cancel', params=params, signed=True)
            return str(response_data) if response_data else None
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise

    def batch_place_orders(self, orders: List[Order]) -> List[str]:
        """
        Batch place orders.
        """
        orders_json = []
        for order in orders:
            sodex_symbol = self._convert_symbol(order.symbol)
            orders_json.append({
                'direction': order.side.upper(),
                'price': f"{order.price:.2f}",
                'symbol': sodex_symbol,
                'totalAmount': f"{order.quantity:.4f}",
                'tradeType': order.type.upper(),
            })
        params = {'ordersJsonStr': json.dumps(orders_json)}
        resp = self._make_request('POST', '/spot/v1/u/trade/order/batch/create', params=params, signed=True)
        order_ids = [data["data"] for data in resp]
        return order_ids

    def cancel_orders_by_ids(self, order_ids: List[str]) -> List[str]:
        """
        Cancel multiple orders by their IDs.
        
        Args:
            order_ids: List of order IDs to cancel
            
        Returns:
            List of cancelled order IDs
            
        Raises:
            SodexAPIError: If API request fails
        """
        if not order_ids:
            logger.info('No order IDs provided for cancellation')
            return []
        
        # Filter out empty IDs
        valid_order_ids = [oid.strip() for oid in order_ids if oid and oid.strip()]
        
        if not valid_order_ids:
            logger.info('No valid order IDs to cancel')
            return []
        
        params = {'orderIdsJson': json.dumps(valid_order_ids)}
        
        try:
            response_data = self._make_request('POST', '/spot/v1/u/trade/order/batch/cancel', params=params, signed=True)
            result = response_data if isinstance(response_data, list) else []
            logger.info(f'Batch cancelled {len(result)} orders')
            return result
        except Exception as e:
            logger.error(f"Failed to batch cancel orders: {e}")
            raise

    def cancel_all_orders(self, symbol: str) -> List[str]:
        """
        Cancel all open orders for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            List of cancelled order IDs
        """
        try:
            orders = self.get_open_orders(symbol)
            order_ids = [order.order_id for order in orders if order.order_id]
            
            if order_ids:
                result = self.cancel_orders_by_ids(order_ids)
                logger.info(f'Cancelled all orders for {symbol}: {len(result)} orders')
                return result
            else:
                logger.info(f'No open orders to cancel for {symbol}')
                return []
        except Exception as e:
            logger.error(f"Failed to cancel all orders for {symbol}: {e}")
            raise
    
    def get_open_orders(self, symbol: str) -> List[Order]:
        """
        Get all open orders for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            List of Order objects
            
        Raises:
            SodexAPIError: If API request fails
        """
        if not symbol or not symbol.strip():
            raise ValueError("Symbol cannot be empty")
        
        sodex_symbol = self._convert_symbol(symbol)
        orders = []
        
        try:
            # Get orders with state=1 (pending) and state=2 (partially filled)
            for state in [1, 2]:
                orders.extend(self._get_orders_by_state(sodex_symbol, state))
            
            return [self._format_order(order_data) for order_data in orders]
        except Exception as e:
            logger.error(f"Failed to get open orders for {symbol}: {e}")
            raise

    def get_order_history(self, 
                         symbol: Optional[str] = None,
                         start_time: Optional[int] = None,
                         end_time: Optional[int] = None,
                         limit: Optional[int] = None) -> List[Order]:
        """
        Get historical orders.
        
        Args:
            symbol: Trading symbol (optional)
            start_time: Start time in milliseconds (optional)
            end_time: End time in milliseconds (optional)
            limit: Maximum number of orders to return (optional)
            
        Returns:
            List of Order objects
            
        Raises:
            SodexAPIError: If API request fails
        """
        params = {}
        
        if symbol:
            params['symbol'] = self._convert_symbol(symbol)
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        if limit:
            params['limit'] = limit
        
        try:
            response_data = self._make_request('GET', '/spot/v1/u/trade/order/history', params=params, signed=True)
            
            if not isinstance(response_data, dict):
                return []
            
            items = response_data.get('items', [])
            return [self._format_order(order_data) for order_data in items]
        except Exception as e:
            logger.error(f"Failed to get order history: {e}")
            raise

    def get_order_fills(self, 
                       order_id: Optional[str] = None,
                       symbol: Optional[str] = None,
                       page: int = 1,
                       size: int = 10) -> List[OrderFill]:
        """
        Get order fill details.
        
        Args:
            order_id: Order ID (optional)
            symbol: Trading symbol (optional)
            page: Page number
            size: Page size
            
        Returns:
            List of OrderFill objects
            
        Raises:
            SodexAPIError: If API request fails
        """
        params = {
            'page': page,
            'size': size
        }
        
        if order_id:
            params['orderId'] = order_id
        if symbol:
            params['symbol'] = self._convert_symbol(symbol)
        
        try:
            response_data = self._make_request('GET', '/spot/v1/u/trade/order/deal', params=params, signed=True)
            
            if not isinstance(response_data, dict):
                return []
            
            items = response_data.get('items', [])
            fills = []
            
            for fill_data in items:
                try:
                    fill = OrderFill(
                        order_id=str(fill_data.get('orderId', '')),
                        exec_id=str(fill_data.get('execId', '')),
                        symbol=self._convert_symbol(fill_data.get('symbol', ''), reverse=True),
                        quantity=float(fill_data.get('quantity', 0)),
                        price=float(fill_data.get('price', 0)),
                        fee=float(fill_data.get('fee', 0)),
                        fee_coin=fill_data.get('feeCoin', ''),
                        side=fill_data.get('orderSide', ''),
                        timestamp=int(fill_data.get('timestamp', 0))
                    )
                    fills.append(fill)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping invalid fill data: {fill_data}, error: {e}")
            
            return fills
        except Exception as e:
            logger.error(f"Failed to get order fills: {e}")
            raise

    def get_server_time(self) -> int:
        """
        Get server time.
        
        Returns:
            Server timestamp in milliseconds
            
        Raises:
            SodexAPIError: If API request fails
        """
        try:
            response_data = self._make_request('GET', '/spot/v1/p/time', signed=False)
            return int(response_data)
        except Exception as e:
            logger.error(f"Failed to get server time: {e}")
            raise

    def get_klines(self, 
                  symbol: str,
                  interval: str,
                  limit: Optional[int] = None,
                  start_time: Optional[int] = None,
                  end_time: Optional[int] = None) -> List[KlineData]:
        """
        Get kline/candlestick data.
        
        Args:
            symbol: Trading symbol
            interval: Kline interval (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)
            limit: Number of klines to return (max 1500)
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
            
        Returns:
            List of KlineData objects
            
        Raises:
            SodexAPIError: If API request fails
            ValueError: If parameters are invalid
        """
        if not symbol or not symbol.strip():
            raise ValueError("Symbol cannot be empty")
        if not interval or not interval.strip():
            raise ValueError("Interval cannot be empty")
        
        valid_intervals = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M']
        if interval not in valid_intervals:
            raise ValueError(f"Invalid interval. Must be one of: {valid_intervals}")
        
        sodex_symbol = self._convert_symbol(symbol)
        params = {
            'symbol': sodex_symbol,
            'interval': interval
        }
        
        if limit:
            params['limit'] = limit
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        try:
            response_data = self._make_request('GET', '/spot/v1/p/quotation/kline', params=params, signed=False)
            
            if not isinstance(response_data, list):
                return []
            
            klines = []
            for kline_data in response_data:
                try:
                    kline = KlineData(
                        symbol=self._convert_symbol(kline_data.get('s', ''), reverse=True),
                        timestamp=int(kline_data.get('t', 0)),
                        open_price=float(kline_data.get('o', 0)),
                        high_price=float(kline_data.get('h', 0)),
                        low_price=float(kline_data.get('l', 0)),
                        close_price=float(kline_data.get('c', 0)),
                        volume=float(kline_data.get('a', 0)),
                        quote_volume=float(kline_data.get('v', 0))
                    )
                    klines.append(kline)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping invalid kline data: {kline_data}, error: {e}")
            
            return klines
        except Exception as e:
            logger.error(f"Failed to get klines for {symbol}: {e}")
            raise

    def get_ticker(self, symbol: str) -> Optional[TickerData]:
        """
        Get 24hr ticker price change statistics for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            TickerData object or None if not found
            
        Raises:
            SodexAPIError: If API request fails
        """
        if not symbol or not symbol.strip():
            raise ValueError("Symbol cannot be empty")
        
        sodex_symbol = self._convert_symbol(symbol)
        params = {'symbol': sodex_symbol}
        
        try:
            response_data = self._make_request('GET', '/spot/v1/p/quotation/trend/ticker', params=params, signed=False)
            
            if not response_data:
                return None
            
            return TickerData(
                symbol=self._convert_symbol(response_data.get('s', ''), reverse=True),
                timestamp=int(response_data.get('t', 0)),
                open_price=float(response_data.get('o', 0)),
                high_price=float(response_data.get('h', 0)),
                low_price=float(response_data.get('l', 0)),
                close_price=float(response_data.get('c', 0)),
                volume=float(response_data.get('a', 0)),
                quote_volume=float(response_data.get('v', 0)),
                price_change_percent=float(response_data.get('r', 0))
            )
        except Exception as e:
            logger.error(f"Failed to get ticker for {symbol}: {e}")
            raise

    def get_all_tickers(self) -> List[TickerData]:
        """
        Get 24hr ticker price change statistics for all symbols.
        
        Returns:
            List of TickerData objects
            
        Raises:
            SodexAPIError: If API request fails
        """
        try:
            response_data = self._make_request('GET', '/spot/v1/p/quotation/tickers', signed=False)
            
            if not isinstance(response_data, list):
                return []
            
            tickers = []
            for ticker_data in response_data:
                try:
                    ticker = TickerData(
                        symbol=self._convert_symbol(ticker_data.get('s', ''), reverse=True),
                        timestamp=int(ticker_data.get('t', 0)),
                        open_price=float(ticker_data.get('o', 0)),
                        high_price=float(ticker_data.get('h', 0)),
                        low_price=float(ticker_data.get('l', 0)),
                        close_price=float(ticker_data.get('c', 0)),
                        volume=float(ticker_data.get('a', 0)),
                        quote_volume=float(ticker_data.get('v', 0)),
                        price_change_percent=float(ticker_data.get('r', 0))
                    )
                    tickers.append(ticker)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping invalid ticker data: {ticker_data}, error: {e}")
            
            return tickers
        except Exception as e:
            logger.error(f"Failed to get all tickers: {e}")
            raise

    def get_recent_trades(self, symbol: str, limit: int = 100) -> List[TradeData]:
        """
        Get recent trades for a symbol.
        
        Args:
            symbol: Trading symbol
            limit: Number of trades to return
            
        Returns:
            List of TradeData objects
            
        Raises:
            SodexAPIError: If API request fails
            ValueError: If parameters are invalid
        """
        if not symbol or not symbol.strip():
            raise ValueError("Symbol cannot be empty")
        if limit <= 0:
            raise ValueError("Limit must be positive")
        
        sodex_symbol = self._convert_symbol(symbol)
        params = {
            'symbol': sodex_symbol,
            'num': limit
        }
        
        try:
            response_data = self._make_request('GET', '/spot/v1/p/quotation/deal', params=params, signed=False)
            
            if not isinstance(response_data, list):
                return []
            
            trades = []
            for trade_data in response_data:
                try:
                    trade = TradeData(
                        symbol=self._convert_symbol(trade_data.get('s', ''), reverse=True),
                        timestamp=int(trade_data.get('t', 0)),
                        price=float(trade_data.get('p', 0)),
                        quantity=float(trade_data.get('a', 0)),
                        side=trade_data.get('m', '')
                    )
                    trades.append(trade)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping invalid trade data: {trade_data}, error: {e}")
            
            return trades
        except Exception as e:
            logger.error(f"Failed to get recent trades for {symbol}: {e}")
            raise

    def get_websocket_token(self) -> str:
        """
        Get WebSocket authentication token.
        
        Returns:
            WebSocket token string
            
        Raises:
            SodexAPIError: If API request fails
        """
        try:
            response_data = self._make_request('GET', '/spot/v1/u/ws/token', signed=True)
            return str(response_data)
        except Exception as e:
            logger.error(f"Failed to get WebSocket token: {e}")
            raise

    def get_symbol_list(self) -> List[SymbolInfo]:
        """
        Get list of all available trading symbols with their configuration.
        
        Returns:
            List of SymbolInfo objects containing symbol configuration details
            
        Raises:
            SodexAPIError: If API request fails
        """
        try:
            # Use the specific URL for symbol list endpoint
            url = f"{Config.SODEX_BASE_URL_EXT}/pro/p/symbol/list"
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            response_data = self._handle_response(response.json())
            
            if not isinstance(response_data, list):
                logger.error("Invalid symbol list response format")
                return []
            
            symbols = []
            for symbol_data in response_data:
                try:
                    symbol_info = SymbolInfo(
                        id=int(symbol_data.get('id', 0)),
                        symbol=symbol_data.get('symbol', ''),
                        name=symbol_data.get('name'),
                        lever=float(symbol_data['lever']) if symbol_data.get('lever') is not None else None,
                        risk_rate=float(symbol_data['riskRate']) if symbol_data.get('riskRate') is not None else None,
                        trade_switch=bool(symbol_data.get('tradeSwitch', False)),
                        buy_coin=symbol_data.get('buyCoin', ''),
                        sell_coin=symbol_data.get('sellCoin', ''),
                        buy_coin_precision=int(symbol_data.get('buyCoinPrecision', 0)),
                        buy_coin_display_precision=int(symbol_data.get('buyCoinDisplayPrecision', 0)),
                        sell_coin_precision=int(symbol_data.get('sellCoinPrecision', 0)),
                        sell_coin_display_precision=int(symbol_data.get('sellCoinDisplayPrecision', 0)),
                        quantity_precision=int(symbol_data.get('quantityPrecision', 0)),
                        price_precision=int(symbol_data.get('pricePrecision', 0)),
                        support_order_type=symbol_data.get('supportOrderType', ''),
                        support_time_in_force=symbol_data.get('supportTimeInForce', ''),
                        min_price=float(symbol_data['minPrice']) if symbol_data.get('minPrice') is not None else None,
                        min_qty=symbol_data.get('minQty', '0'),
                        min_notional=float(symbol_data['minNotional']) if symbol_data.get('minNotional') is not None else None,
                        multiplier_down=symbol_data.get('multiplierDown', '0'),
                        multiplier_up=symbol_data.get('multiplierUp', '0'),
                        maker_fee=symbol_data.get('makerFee', '0'),
                        taker_fee=symbol_data.get('takerFee', '0'),
                        market_take_bound=symbol_data.get('marketTakeBound', '0'),
                        depth_precision_merge=int(symbol_data.get('depthPrecisionMerge', 0)),
                        onboard_date=int(symbol_data.get('onboardDate', 0)),
                        sequence=int(symbol_data.get('sequence', 0)),
                        set_type=int(symbol_data.get('setType', 0)),
                        uids=symbol_data.get('uids'),
                        hot=bool(symbol_data.get('hot', False))
                    )
                    symbols.append(symbol_info)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping invalid symbol data: {symbol_data}, error: {e}")
            return symbols
        except Exception as e:
            logger.error(f"Failed to get symbol list: {e}")
            raise
    
    def _get_orders_by_state(self, sodex_symbol: str, state: int) -> List[Dict[str, Any]]:
        """
        Get orders by state with pagination.
        
        Args:
            sodex_symbol: Symbol in Sodex format
            state: Order state (1=pending, 2=partially filled)
            
        Returns:
            List of order data dictionaries
        """
        orders = []
        page = 1
        
        while True:
            params = {
                'page': page,
                'size': MAX_PAGE_SIZE,
                'state': state,
                'symbol': sodex_symbol
            }
            
            response_data = self._make_request('GET', '/spot/v1/u/trade/order/list', params=params, signed=True)
            
            if not isinstance(response_data, dict):
                break
            
            items = response_data.get('items', [])
            orders.extend(items)
            
            # Check if we have more pages
            current_page = response_data.get('page', 0)
            page_size = response_data.get('ps', 0)
            total = response_data.get('total', 0)
            
            if current_page * page_size >= total:
                break
            
            page += 1
        
        return orders
    
    def get_order_info(self, symbol: str, order_id: str) -> Order:
        """
        Get detailed information about a specific order.
        
        Args:
            symbol: Trading symbol
            order_id: Order ID
            
        Returns:
            Order object
            
        Raises:
            SodexAPIError: If API request fails
            ValueError: If parameters are invalid
        """
        if not order_id or not order_id.strip():
            raise ValueError("Order ID cannot be empty")
        
        params = {'orderId': order_id.strip()}
        
        try:
            response_data = self._make_request('GET', '/spot/v1/u/trade/order/detail', params=params, signed=True)
            return self._format_order(response_data)
        except Exception as e:
            logger.error(f"Failed to get order info for {order_id}: {e}")
            raise
    
    def _format_order(self, raw_order: Dict[str, Any]) -> Order:
        """
        Format raw order data into Order object.
        
        Args:
            raw_order: Raw order data from API
            
        Returns:
            Formatted Order object
            
        Raises:
            ValueError: If order data is invalid
        """
        try:
            return Order(
                order_id=str(raw_order.get('orderId', '')),
                client_order_id=raw_order.get('clientOrderId'),
                symbol=self._convert_symbol(raw_order.get('symbol', ''), reverse=True),
                side=raw_order.get('orderSide', '').upper(),
                quantity=float(raw_order.get('origQty', 0)),
                price=float(raw_order.get('price', 0)),
                type=raw_order.get('orderType', ''),
                status=raw_order.get('state', ''),
                timestamp=int(raw_order.get('createdTime', 0))
            )
        except (ValueError, TypeError) as e:
            raise SodexAPIError(f"Invalid order data format: {e}")

    def _format_orderbook(self, raw_orderbook: Dict[str, Any]) -> Orderbook:
        """
        Format raw orderbook data into Orderbook object.
        
        Args:
            raw_orderbook: Raw orderbook data from API
            
        Returns:
            Formatted Orderbook object
            
        Raises:
            SodexAPIError: If orderbook data is invalid
        """
        try:
            return Orderbook( 
                symbol=self._convert_symbol(raw_orderbook.get('s', ''), reverse=True),
                timestamp=raw_orderbook.get("t", int(time.time() * 1000)),
                bids=[
                    OBItem(price=float(bid[0]), quantity=float(bid[1])) 
                    for bid in raw_orderbook.get('b', [])
                    if len(bid) >= 2 and float(bid[1]) > 0
                ],
                asks=[
                    OBItem(price=float(ask[0]), quantity=float(ask[1])) 
                    for ask in raw_orderbook.get('a', [])
                    if len(ask) >= 2 and float(ask[1]) > 0
                ]
            )
        except (KeyError, ValueError, TypeError) as e:
            raise SodexAPIError(f"Invalid orderbook data format: {e}")