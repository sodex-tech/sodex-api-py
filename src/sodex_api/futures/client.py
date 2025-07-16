"""Futures trading client for Sodex API."""

import json
from typing import Dict, List, Optional, Any
from loguru import logger

from ..core import BaseClient
from ..core.exceptions import (
    SodexAPIError,
    InvalidOrderError,
    MarketDataError
)
from .models import (
    FuturesBalance,
    FuturesOrder,
    FuturesOrderbook,
    FuturesSymbol,
    FuturesTicker,
    FuturesKline,
    FuturesTrade,
    FuturesOrderFill,
    PositionSide,
    TimeInForce
)


class FuturesClient(BaseClient):
    """Client for interacting with Sodex Futures API."""
    
    def __init__(self, api_key: str, secret_key: str, base_url: str, timeout: float = 10.0):
        super().__init__(api_key, secret_key, base_url, timeout)
    
    # Public API Methods (No Authentication Required)
    
    def get_server_time(self) -> int:
        """
        Get server time.
        
        Returns:
            Server timestamp in milliseconds
            
        Raises:
            SodexAPIError: If API request fails
        """
        try:
            response_data = self._make_request('GET', '/fut/v1/public/time', signed=False)
            return int(response_data)
        except Exception as e:
            logger.error(f"Failed to get server time: {e}")
            raise
    
    def get_symbol_detail(self, symbol: str) -> FuturesSymbol:
        """
        Get futures symbol details.
        
        Args:
            symbol: Trading symbol (e.g., "btc_usdc")
            
        Returns:
            FuturesSymbol object
            
        Raises:
            SodexAPIError: If API request fails
            ValueError: If parameters are invalid
        """
        if not symbol or not symbol.strip():
            raise ValueError("Symbol cannot be empty")
        
        params = {'symbol': symbol.lower()}
        
        try:
            response_data = self._make_request('GET', '/fut/v1/public/symbol/detail', params=params, signed=False)
            return self._format_symbol(response_data)
        except Exception as e:
            logger.error(f"Failed to get symbol detail for {symbol}: {e}")
            raise
    
    def get_ticker(self, symbol: str) -> FuturesTicker:
        """
        Get 24hr ticker for a futures symbol.
        
        Args:
            symbol: Trading symbol (e.g., "BTC_USDC")
            
        Returns:
            FuturesTicker object
            
        Raises:
            MarketDataError: If API request fails
        """
        if not symbol or not symbol.strip():
            raise ValueError("Symbol cannot be empty")
        
        params = {'symbol': symbol.upper()}
        
        try:
            response_data = self._make_request('GET', '/fut/v1/public/q/ticker', params=params, signed=False)
            return self._format_ticker(response_data)
        except Exception as e:
            logger.error(f"Failed to get ticker for {symbol}: {e}")
            raise MarketDataError(f"Failed to get ticker data: {str(e)}")
    
    def get_all_tickers(self) -> List[FuturesTicker]:
        """
        Get 24hr tickers for all futures symbols.
        
        Returns:
            List of FuturesTicker objects
            
        Raises:
            MarketDataError: If API request fails
        """
        try:
            response_data = self._make_request('GET', '/fut/v1/public/q/tickers', signed=False)
            
            if not isinstance(response_data, list):
                return []
            
            return [self._format_ticker(ticker_data) for ticker_data in response_data]
        except Exception as e:
            logger.error(f"Failed to get all tickers: {e}")
            raise MarketDataError(f"Failed to get ticker data: {str(e)}")
    
    def get_klines(self,
                  symbol: str,
                  interval: str,
                  limit: Optional[int] = None,
                  start_time: Optional[int] = None,
                  end_time: Optional[int] = None) -> List[FuturesKline]:
        """
        Get kline/candlestick data.
        
        Args:
            symbol: Trading symbol (e.g., "BTC_USDC")
            interval: Kline interval (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)
            limit: Number of klines to return (max 1500)
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
            
        Returns:
            List of FuturesKline objects
            
        Raises:
            MarketDataError: If API request fails
            ValueError: If parameters are invalid
        """
        if not symbol or not symbol.strip():
            raise ValueError("Symbol cannot be empty")
        if not interval or not interval.strip():
            raise ValueError("Interval cannot be empty")
        
        valid_intervals = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M']
        if interval not in valid_intervals:
            raise ValueError(f"Invalid interval. Must be one of: {valid_intervals}")
        
        params = {
            'symbol': symbol.upper(),
            'interval': interval
        }
        
        if limit:
            params['limit'] = limit
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        try:
            response_data = self._make_request('GET', '/fut/v1/public/q/kline', params=params, signed=False)
            
            if not isinstance(response_data, list):
                return []
            
            return [self._format_kline(kline_data) for kline_data in response_data]
        except Exception as e:
            logger.error(f"Failed to get klines for {symbol}: {e}")
            raise MarketDataError(f"Failed to get kline data: {str(e)}")
    
    def get_orderbook(self, symbol: str, level: int = 20) -> FuturesOrderbook:
        """
        Get orderbook for a futures symbol.
        
        Args:
            symbol: Trading symbol (e.g., "BTC_USDC")
            level: Number of price levels (1-50)
            
        Returns:
            FuturesOrderbook object
            
        Raises:
            MarketDataError: If API request fails
            ValueError: If parameters are invalid
        """
        if not symbol or not symbol.strip():
            raise ValueError("Symbol cannot be empty")
        
        if not 1 <= level <= 50:
            raise ValueError("Level must be between 1 and 50")
        
        params = {
            'symbol': symbol.upper(),
            'level': level
        }
        
        try:
            response_data = self._make_request('GET', '/fut/v1/public/q/depth', params=params, signed=False)
            return self._format_orderbook(response_data)
        except Exception as e:
            logger.error(f"Failed to get orderbook for {symbol}: {e}")
            raise MarketDataError(f"Failed to get orderbook data: {str(e)}")
    
    def get_recent_trades(self, symbol: str, num: int = 100) -> List[FuturesTrade]:
        """
        Get recent trades for a futures symbol.
        
        Args:
            symbol: Trading symbol (e.g., "BTC_USDC")
            num: Number of trades to return
            
        Returns:
            List of FuturesTrade objects
            
        Raises:
            MarketDataError: If API request fails
            ValueError: If parameters are invalid
        """
        if not symbol or not symbol.strip():
            raise ValueError("Symbol cannot be empty")
        if num <= 0:
            raise ValueError("Number of trades must be positive")
        
        params = {
            'symbol': symbol.upper(),
            'num': num
        }
        
        try:
            response_data = self._make_request('GET', '/fut/v1/public/q/deal', params=params, signed=False)
            
            if not isinstance(response_data, list):
                return []
            
            return [self._format_trade(trade_data) for trade_data in response_data]
        except Exception as e:
            logger.error(f"Failed to get recent trades for {symbol}: {e}")
            raise MarketDataError(f"Failed to get trade data: {str(e)}")
    
    # Private API Methods (Authentication Required)
    
    def get_balances(self, balance_type: Optional[str] = None) -> List[FuturesBalance]:
        """
        Get futures account balances.
        
        Args:
            balance_type: Optional balance type filter
            
        Returns:
            List of FuturesBalance objects
            
        Raises:
            SodexAPIError: If API request fails
        """
        params = {}
        if balance_type:
            params['balanceType'] = balance_type
        
        try:
            response_data = self._make_request('GET', '/fut/v1/balance/list', params=params, signed=True)
            
            if not isinstance(response_data, list):
                logger.error("Invalid balance response format")
                return []
            
            balances = []
            for balance_data in response_data:
                try:
                    balance = FuturesBalance(
                        coin=balance_data.get("coin", ""),
                        balance_type=balance_data.get("balanceType", ""),
                        wallet_balance=float(balance_data.get("walletBalance", 0)),
                        available_balance=float(balance_data.get("availableBalance", 0)),
                        open_order_margin_frozen=float(balance_data.get("openOrderMarginFrozen", 0)),
                        isolated_margin=float(balance_data.get("isolatedMargin", 0)),
                        crossed_margin=float(balance_data.get("crossedMargin", 0)),
                        bonus=float(balance_data.get("bonus", 0))
                    )
                    balances.append(balance)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping invalid balance data: {balance_data}, error: {e}")
            
            return balances
        except Exception as e:
            logger.error(f"Failed to get balances: {e}")
            raise
    
    def place_order(self,
                   symbol: str,
                   order_side: str,
                   order_type: str,
                   position_side: str,
                   quantity: float,
                   price: Optional[float] = None,
                   client_order_id: Optional[str] = None,
                   leverage: Optional[int] = None,
                   time_in_force: str = "GTC",
                   reduce_only: bool = False,
                   trigger_profit_price: Optional[float] = None,
                   trigger_stop_price: Optional[float] = None) -> str:
        """
        Place a futures order.
        
        Args:
            symbol: Trading symbol
            order_side: Order side ("BUY" or "SELL")
            order_type: Order type ("LIMIT" or "MARKET")
            position_side: Position side ("LONG" or "SHORT")
            quantity: Order quantity
            price: Order price (required for LIMIT orders)
            client_order_id: Custom order ID
            leverage: Leverage multiplier
            time_in_force: Time in force (GTC, IOC, FOK, GTX)
            reduce_only: Whether this is a reduce-only order
            trigger_profit_price: Take profit price
            trigger_stop_price: Stop loss price
            
        Returns:
            Order ID
            
        Raises:
            InvalidOrderError: If order parameters are invalid
            SodexAPIError: If API request fails
        """
        # Validate required parameters
        if not symbol or not symbol.strip():
            raise InvalidOrderError("Symbol cannot be empty")
        if order_side.upper() not in ("BUY", "SELL"):
            raise InvalidOrderError("Order side must be 'BUY' or 'SELL'")
        if order_type.upper() not in ("LIMIT", "MARKET"):
            raise InvalidOrderError("Order type must be 'LIMIT' or 'MARKET'")
        if position_side.upper() not in ("LONG", "SHORT"):
            raise InvalidOrderError("Position side must be 'LONG' or 'SHORT'")
        if quantity <= 0:
            raise InvalidOrderError("Quantity must be positive")
        if order_type.upper() == "LIMIT" and (price is None or price <= 0):
            raise InvalidOrderError("Price is required for LIMIT orders")
        
        params = {
            'symbol': symbol.lower(),
            'orderSide': order_side.upper(),
            'orderType': order_type.upper(),
            'positionSide': position_side.upper(),
            'origQty': str(quantity)
        }
        
        if price is not None:
            params['price'] = str(price)
        if client_order_id:
            params['clientOrderId'] = client_order_id
        if leverage:
            params['leverage'] = leverage
        if time_in_force:
            params['timeInForce'] = time_in_force
        if reduce_only:
            params['reduceOnly'] = reduce_only
        if trigger_profit_price:
            params['triggerProfitPrice'] = str(trigger_profit_price)
        if trigger_stop_price:
            params['triggerStopPrice'] = str(trigger_stop_price)
        
        logger.debug(f'Placing futures order: {params}')
        
        try:
            response_data = self._make_request('POST', '/fut/v1/order/create', params=params, signed=True)
            return str(response_data) if response_data else None
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise
    
    def cancel_order(self, order_id: str) -> str:
        """
        Cancel a futures order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            Cancelled order ID
            
        Raises:
            InvalidOrderError: If order ID is invalid
            SodexAPIError: If API request fails
        """
        if not order_id or not order_id.strip():
            raise InvalidOrderError("Order ID cannot be empty")
        
        params = {'orderId': order_id.strip()}
        
        try:
            response_data = self._make_request('POST', '/fut/v1/order/cancel', params=params, signed=True)
            return str(response_data) if response_data else None
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise
    
    def batch_cancel_orders(self, order_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Cancel multiple futures orders.
        
        Args:
            order_ids: List of order IDs to cancel
            
        Returns:
            List of cancellation results
            
        Raises:
            InvalidOrderError: If parameters are invalid
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
        
        if len(valid_order_ids) > 20:
            raise InvalidOrderError("Maximum 20 orders can be cancelled at once")
        
        params = {'orderIds': json.dumps(valid_order_ids)}
        
        try:
            response_data = self._make_request('POST', '/fut/v1/order/cancel-batch', params=params, signed=True)
            result = response_data if isinstance(response_data, list) else []
            logger.info(f'Batch cancelled {len(result)} futures orders')
            return result
        except Exception as e:
            logger.error(f"Failed to batch cancel orders: {e}")
            raise
    
    def get_order_detail(self, order_id: str) -> FuturesOrder:
        """
        Get futures order details.
        
        Args:
            order_id: Order ID
            
        Returns:
            FuturesOrder object
            
        Raises:
            InvalidOrderError: If order ID is invalid
            SodexAPIError: If API request fails
        """
        if not order_id or not order_id.strip():
            raise InvalidOrderError("Order ID cannot be empty")
        
        params = {'orderId': order_id.strip()}
        
        try:
            response_data = self._make_request('GET', '/fut/v1/order/detail', params=params, signed=True)
            return self._format_order(response_data)
        except Exception as e:
            logger.error(f"Failed to get order detail for {order_id}: {e}")
            raise
    
    def get_orders(self,
                  symbol: Optional[str] = None,
                  state: Optional[str] = None,
                  page: int = 1,
                  size: int = 10,
                  start_time: Optional[int] = None,
                  end_time: Optional[int] = None,
                  contract_type: Optional[str] = None,
                  client_order_id: Optional[str] = None,
                  force_close: Optional[bool] = None) -> Dict[str, Any]:
        """
        Get futures orders with pagination.
        
        Args:
            symbol: Trading symbol filter
            state: Order state filter (UNFINISHED, HISTORY, CANCELED)
            page: Page number (default 1)
            size: Page size (default 10)
            start_time: Start time filter
            end_time: End time filter
            contract_type: Contract type filter
            client_order_id: Client order ID filter
            force_close: Force close filter
            
        Returns:
            Dict containing pagination info and order list
            
        Raises:
            SodexAPIError: If API request fails
        """
        params = {
            'page': page,
            'size': size
        }
        
        if symbol:
            params['symbol'] = symbol.lower()
        if state:
            params['state'] = state
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        if contract_type:
            params['contractType'] = contract_type
        if client_order_id:
            params['clientOrderId'] = client_order_id
        if force_close is not None:
            params['forceClose'] = force_close
        
        try:
            response_data = self._make_request('GET', '/fut/v1/order/list', params=params, signed=True)
            
            if not isinstance(response_data, dict):
                return {'page': 1, 'ps': 0, 'total': 0, 'items': []}
            
            # Format orders in the response
            items = response_data.get('items', [])
            response_data['items'] = [self._format_order(order_data) for order_data in items]
            
            return response_data
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            raise
    
    def get_order_fills(self,
                       symbol: Optional[str] = None,
                       order_id: Optional[str] = None,
                       start_time: Optional[int] = None,
                       end_time: Optional[int] = None,
                       page: int = 1,
                       size: int = 10) -> Dict[str, Any]:
        """
        Get order fill details.
        
        Args:
            symbol: Trading symbol filter
            order_id: Order ID filter
            start_time: Start time filter
            end_time: End time filter
            page: Page number
            size: Page size
            
        Returns:
            Dict containing pagination info and fill list
            
        Raises:
            SodexAPIError: If API request fails
        """
        params = {
            'page': page,
            'size': size
        }
        
        if symbol:
            params['symbol'] = symbol.lower()
        if order_id:
            params['orderId'] = order_id
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        try:
            response_data = self._make_request('GET', '/fut/v1/order/trade-list', params=params, signed=True)
            
            if not isinstance(response_data, dict):
                return {'page': 1, 'ps': 0, 'total': 0, 'items': []}
            
            # Format fills in the response
            items = response_data.get('items', [])
            fills = []
            
            for fill_data in items:
                try:
                    fill = FuturesOrderFill(
                        order_id=str(fill_data.get('orderId', '')),
                        exec_id=str(fill_data.get('execId', '')),
                        symbol=fill_data.get('symbol', ''),
                        quantity=float(fill_data.get('quantity', 0)),
                        price=float(fill_data.get('price', 0)),
                        fee=float(fill_data.get('fee', 0)),
                        fee_coin=fill_data.get('feeCoin', ''),
                        timestamp=int(fill_data.get('timestamp', 0))
                    )
                    fills.append(fill)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping invalid fill data: {fill_data}, error: {e}")
            
            response_data['items'] = fills
            return response_data
        except Exception as e:
            logger.error(f"Failed to get order fills: {e}")
            raise
    
    def get_listen_key(self) -> str:
        """
        Get WebSocket listen key for user data stream.
        
        Returns:
            Listen key string
            
        Raises:
            SodexAPIError: If API request fails
        """
        try:
            response_data = self._make_request('GET', '/fut/v1/user/listen-key', signed=True)
            return str(response_data)
        except Exception as e:
            logger.error(f"Failed to get listen key: {e}")
            raise
    
    # Helper methods
    
    def _format_symbol(self, raw_symbol: Dict[str, Any]) -> FuturesSymbol:
        """Format raw symbol data into FuturesSymbol object."""
        try:
            return FuturesSymbol(
                id=int(raw_symbol.get('id', 0)),
                symbol=raw_symbol.get('symbol', ''),
                contract_type=raw_symbol.get('contractType', ''),
                underlying_type=raw_symbol.get('underlyingType', ''),
                contract_size=float(raw_symbol.get('contractSize', 0)),
                init_leverage=int(raw_symbol.get('initLeverage', 1)),
                init_position_type=raw_symbol.get('initPositionType', ''),
                base_coin=raw_symbol.get('baseCoin', ''),
                quote_coin=raw_symbol.get('quoteCoin', ''),
                quantity_precision=int(raw_symbol.get('quantityPrecision', 0)),
                price_precision=int(raw_symbol.get('pricePrecision', 0)),
                support_order_type=raw_symbol.get('supportOrderType', ''),
                support_time_in_force=raw_symbol.get('supportTimeInForce', ''),
                min_qty=float(raw_symbol.get('minQty', 0)),
                min_notional=float(raw_symbol.get('minNotional', 0)),
                max_notional=float(raw_symbol.get('maxNotional', 0)),
                maker_fee=float(raw_symbol.get('makerFee', 0)),
                taker_fee=float(raw_symbol.get('takerFee', 0)),
                min_step_price=float(raw_symbol.get('minStepPrice', 0)),
                trade_switch=bool(raw_symbol.get('tradeSwitch', False)),
                state=int(raw_symbol.get('state', 0)),
                support_position_type=raw_symbol.get('supportPositionType', ''),
                max_open_orders=int(raw_symbol.get('maxOpenOrders', 0)),
                max_entrusts=int(raw_symbol.get('maxEntrusts', 0)),
                liquidation_fee=float(raw_symbol.get('liquidationFee', 0)),
                labels=raw_symbol.get('labels'),
                onboard_date=raw_symbol.get('onboardDate'),
                en_name=raw_symbol.get('enName'),
                cn_name=raw_symbol.get('cnName')
            )
        except (ValueError, TypeError) as e:
            raise SodexAPIError(f"Invalid symbol data format: {e}")
    
    def _format_ticker(self, raw_ticker: Dict[str, Any]) -> FuturesTicker:
        """Format raw ticker data into FuturesTicker object."""
        try:
            return FuturesTicker(
                symbol=raw_ticker.get('s', ''),
                timestamp=int(raw_ticker.get('t', 0)),
                close_price=float(raw_ticker.get('c', 0)),
                open_price=float(raw_ticker.get('o', 0)),
                high_price=float(raw_ticker.get('h', 0)),
                low_price=float(raw_ticker.get('l', 0)),
                volume=float(raw_ticker.get('a', 0)),
                quote_volume=float(raw_ticker.get('v', 0)),
                price_change_percent=float(raw_ticker.get('r', 0))
            )
        except (ValueError, TypeError) as e:
            raise SodexAPIError(f"Invalid ticker data format: {e}")
    
    def _format_kline(self, raw_kline: Dict[str, Any]) -> FuturesKline:
        """Format raw kline data into FuturesKline object."""
        try:
            return FuturesKline(
                symbol=raw_kline.get('s', ''),
                timestamp=int(raw_kline.get('t', 0)),
                open_price=float(raw_kline.get('o', 0)),
                high_price=float(raw_kline.get('h', 0)),
                low_price=float(raw_kline.get('l', 0)),
                close_price=float(raw_kline.get('c', 0)),
                volume=float(raw_kline.get('a', 0)),
                quote_volume=float(raw_kline.get('v', 0))
            )
        except (ValueError, TypeError) as e:
            raise SodexAPIError(f"Invalid kline data format: {e}")
    
    def _format_orderbook(self, raw_orderbook: Dict[str, Any]) -> FuturesOrderbook:
        """Format raw orderbook data into FuturesOrderbook object."""
        try:
            return FuturesOrderbook(
                symbol=raw_orderbook.get('s', ''),
                timestamp=int(raw_orderbook.get('t', 0)),
                update_id=int(raw_orderbook.get('u', 0)),
                bids=[[float(bid[0]), float(bid[1])] for bid in raw_orderbook.get('b', [])],
                asks=[[float(ask[0]), float(ask[1])] for ask in raw_orderbook.get('a', [])]
            )
        except (ValueError, TypeError) as e:
            raise SodexAPIError(f"Invalid orderbook data format: {e}")
    
    def _format_trade(self, raw_trade: Dict[str, Any]) -> FuturesTrade:
        """Format raw trade data into FuturesTrade object."""
        try:
            return FuturesTrade(
                symbol=raw_trade.get('s', ''),
                price=float(raw_trade.get('p', 0)),
                quantity=float(raw_trade.get('a', 0)),
                timestamp=int(raw_trade.get('t', 0)),
                side=raw_trade.get('m', '')
            )
        except (ValueError, TypeError) as e:
            raise SodexAPIError(f"Invalid trade data format: {e}")
    
    def _format_order(self, raw_order: Dict[str, Any]) -> FuturesOrder:
        """Format raw order data into FuturesOrder object."""
        try:
            return FuturesOrder(
                order_id=str(raw_order.get('orderId', '')),
                client_order_id=raw_order.get('clientOrderId'),
                symbol=raw_order.get('symbol', ''),
                contract_type=raw_order.get('contractType', ''),
                order_type=raw_order.get('orderType', ''),
                order_side=raw_order.get('orderSide', ''),
                leverage=int(raw_order.get('leverage', 1)),
                position_side=raw_order.get('positionSide', ''),
                time_in_force=raw_order.get('timeInForce', ''),
                close_position=bool(raw_order.get('closePosition', False)),
                price=float(raw_order.get('price', 0)),
                orig_qty=float(raw_order.get('origQty', 0)),
                avg_price=float(raw_order.get('avgPrice', 0)),
                executed_qty=float(raw_order.get('executedQty', 0)),
                margin_frozen=float(raw_order.get('marginFrozen', 0)),
                trigger_profit_price=float(raw_order.get('triggerProfitPrice', 0)) if raw_order.get('triggerProfitPrice') else None,
                trigger_stop_price=float(raw_order.get('triggerStopPrice', 0)) if raw_order.get('triggerStopPrice') else None,
                source_id=raw_order.get('sourceId'),
                force_close=bool(raw_order.get('forceClose', False)),
                trade_fee=float(raw_order.get('tradeFee', 0)),
                close_profit=float(raw_order.get('closeProfit', 0)) if raw_order.get('closeProfit') else None,
                state=raw_order.get('state', ''),
                created_time=int(raw_order.get('createdTime', 0)),
                updated_time=int(raw_order.get('updatedTime', 0))
            )
        except (ValueError, TypeError) as e:
            raise SodexAPIError(f"Invalid order data format: {e}")