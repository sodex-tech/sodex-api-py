import asyncio
import json
import websockets
from typing import Dict, Optional, Callable, Any, Union, Literal
from dataclasses import dataclass
from loguru import logger
from enum import Enum

from .client import SodexClient, SodexAPIError
from .models import Orderbook, OBItem, TradeData, TickerData, OrderSide


class SubscriptionType(Enum):
    """WebSocket subscription types."""
    SYMBOL = "subSymbol"
    KLINE = "subKline"
    STATS = "subStats"
    USER = "subUser"


@dataclass
class WebSocketConfig:
    """WebSocket connection configuration."""
    ping_interval: int = 25
    ping_timeout: int = 10
    reconnect_interval: int = 5
    max_reconnect_attempts: int = 10


@dataclass
class DepthData:
    """Represents depth/orderbook update data."""
    id: str
    symbol: str
    side: Literal["ASK", "BID"]
    price: float
    quantity: float
    timestamp: int


@dataclass
class KlineStreamData:
    """Represents kline stream data."""
    symbol: str
    open_price: float
    close_price: float
    high_price: float
    low_price: float
    volume: float
    quote_volume: float
    interval: str
    timestamp: int

@dataclass
class UserBalanceData:
    """Represents user balance update data."""
    coin: str
    balance_type: int
    balance: float
    freeze: float
    available_balance: float
    estimated_total_amount: float
    estimated_cny_amount: float
    estimated_available_amount: float
    estimated_coin_type: str


@dataclass
class UserOrderData:
    """Represents user order update data."""
    order_id: str
    balance_type: int
    order_type: OrderSide
    symbol: str
    price: float
    direction: OrderSide
    orig_qty: float
    avg_price: float
    executed_qty: float
    state: int  # 1=new, 2=partial, 3=filled, 4=cancelled
    create_time: int


@dataclass
class UserTradeData:
    """Represents user trade execution data."""
    order_id: str
    price: float
    quantity: float
    margin_unfrozen: float
    timestamp: int


@dataclass
class SystemMessage:
    """Represents system notification message."""
    id: int
    title: str
    content: str
    agg_type: str
    detail_type: str
    created_time: int
    all_scope: bool
    user_id: int
    read: bool

SOCKET_URL_PATH = "/spot/v1/ws/socket"

class SodexWebSocketClient:
    """WebSocket client for Sodex Exchange real-time data."""
    
    def __init__(self, host: str, config: Optional[WebSocketConfig] = None):
        self.url = f'{host}{SOCKET_URL_PATH}'
        self.config = config or WebSocketConfig()
        self.sodex_client = SodexClient()
        self.websocket = None
        self.is_connected = False
        self.is_authenticated = False
        self.auth_token = None
        self.subscriptions = set()
        self.callbacks = {}
        self.reconnect_count = 0
        self._ping_task = None
        self._listen_task = None
        
    async def connect(self) -> bool:
        """
        Connect to WebSocket server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to WebSocket: {self.url}")
            self.websocket = await websockets.connect(
                self.url,
                ping_interval=None,  # We handle ping manually
                ping_timeout=self.config.ping_timeout
            )
            self.is_connected = True
            self.reconnect_count = 0
            logger.info("WebSocket connected successfully")
            
            # Start ping task
            self._ping_task = asyncio.create_task(self._ping_loop())
            
            return True
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket server."""
        logger.info("Disconnecting from WebSocket")
        self.is_connected = False
        self.is_authenticated = False
        
        # Cancel tasks
        if self._ping_task:
            self._ping_task.cancel()
        if self._listen_task:
            self._listen_task.cancel()
        
        # Close connection
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        logger.info("WebSocket disconnected")
    
    async def authenticate(self) -> bool:
        """
        Authenticate for user data subscriptions.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            logger.info("Getting WebSocket authentication token")
            self.auth_token = self.sodex_client.get_websocket_token()
            self.is_authenticated = True
            logger.info("WebSocket authentication successful")
            return True
        except Exception as e:
            logger.error(f"Failed to authenticate WebSocket: {e}")
            self.is_authenticated = False
            return False
    
    async def subscribe_symbol(self, symbol: str, callback: Callable[[Union[DepthData, Orderbook, TradeData]], None]):
        """
        Subscribe to symbol data (depth and trades).
        
        Args:
            symbol: Trading symbol
            callback: Callback function for data updates
        """
        if not self.is_connected:
            raise SodexAPIError("WebSocket not connected")
        
        sodex_symbol = self.sodex_client._convert_symbol(symbol)
        
        subscription = {
            "sub": SubscriptionType.SYMBOL.value,
            "symbol": sodex_symbol
        }
        
        await self._send_message(subscription)
        
        callback_key = f"symbol_{sodex_symbol}"
        self.callbacks[callback_key] = callback
        self.subscriptions.add(callback_key)
        
        logger.info(f"Subscribed to symbol data: {symbol}")
    
    async def subscribe_kline(self, symbol: str, interval: str, callback: Callable[[KlineStreamData], None]):
        """
        Subscribe to kline data.
        
        Args:
            symbol: Trading symbol
            interval: Kline interval (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)
            callback: Callback function for kline updates
        """
        if not self.is_connected:
            raise SodexAPIError("WebSocket not connected")
        
        # Convert symbol to Sodex format
        sodex_symbol = self.sodex_client._convert_symbol(symbol)
        
        subscription = {
            "sub": SubscriptionType.KLINE.value,
            "symbol": sodex_symbol,
            "type": interval
        }
        
        await self._send_message(subscription)
        
        # Store callback
        callback_key = f"kline_{sodex_symbol}_{interval}"
        self.callbacks[callback_key] = callback
        self.subscriptions.add(callback_key)
        
        logger.info(f"Subscribed to kline data: {symbol} {interval}")
    
    async def subscribe_stats(self, callback: Callable[[TickerData], None]):
        """
        Subscribe to 24hr statistics data.
        
        Args:
            callback: Callback function for stats updates
        """
        if not self.is_connected:
            raise SodexAPIError("WebSocket not connected")
        
        subscription = {
            "sub": SubscriptionType.STATS.value
        }
        
        await self._send_message(subscription)
        
        # Store callback
        callback_key = "stats"
        self.callbacks[callback_key] = callback
        self.subscriptions.add(callback_key)
        
        logger.info("Subscribed to statistics data")
    
    async def subscribe_user_data(self, 
                                 balance_callback: Optional[Callable[[UserBalanceData], None]] = None,
                                 order_callback: Optional[Callable[[UserOrderData], None]] = None,
                                 trade_callback: Optional[Callable[[UserTradeData], None]] = None):
        """
        Subscribe to user data (balance, orders, trades).
        
        Args:
            balance_callback: Callback for balance updates
            order_callback: Callback for order updates
            trade_callback: Callback for trade updates
        """
        if not self.is_connected:
            raise SodexAPIError("WebSocket not connected")
        
        if not self.is_authenticated:
            if not await self.authenticate():
                raise SodexAPIError("Failed to authenticate for user data")
        
        subscription = {
            "sub": SubscriptionType.USER.value,
            "token": self.auth_token
        }
        
        await self._send_message(subscription)
        
        # Store callbacks
        if balance_callback:
            self.callbacks["user_balance"] = balance_callback
        if order_callback:
            self.callbacks["user_order"] = order_callback
        if trade_callback:
            self.callbacks["user_trade"] = trade_callback
        
        self.subscriptions.add("user_data")
        
        logger.info("Subscribed to user data")
    
    async def start_listening(self):
        """Start listening for WebSocket messages."""
        if not self.is_connected:
            raise SodexAPIError("WebSocket not connected")
        
        self._listen_task = asyncio.create_task(self._listen_loop())
        logger.info("Started WebSocket message listening")
    
    async def stop_listening(self):
        """Stop listening for WebSocket messages."""
        if self._listen_task:
            self._listen_task.cancel()
            logger.info("Stopped WebSocket message listening")
    
    async def _send_message(self, message: Dict[str, Any]):
        """Send message to WebSocket server."""
        if not self.websocket:
            raise SodexAPIError("WebSocket not connected")
        
        message_str = json.dumps(message)
        await self.websocket.send(message_str)
        logger.debug(f"Sent WebSocket message: {message_str}")
    
    async def _ping_loop(self):
        """Send periodic ping messages to keep connection alive."""
        while self.is_connected:
            try:
                await asyncio.sleep(self.config.ping_interval)
                if self.websocket and self.is_connected:
                    await self.websocket.send("ping")
                    logger.debug("Sent ping message")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in ping loop: {e}")
                break
    
    async def _listen_loop(self):
        """Listen for WebSocket messages."""
        while self.is_connected:
            try:
                if not self.websocket:
                    break
                
                message = await self.websocket.recv()
                
                # Handle pong response
                if message == "pong":
                    logger.debug("Received pong message")
                    continue

                if message == "succeed":
                    continue
                
                # Parse JSON message
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse WebSocket message: {message}, error: {e}")
                
            except asyncio.CancelledError:
                break
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed")
                self.is_connected = False
                await self._handle_reconnect()
                break
            except Exception as e:
                logger.error(f"Error in listen loop: {e}")
                await asyncio.sleep(1)
    
    async def _handle_message(self, data: Dict[str, Any]):
        """Handle incoming WebSocket message."""
        try:
            res_type = data.get("resType")
            message_data = data.get("data", {})
            
            if res_type == "qDepth":
                await self._handle_depth_data(message_data)
            elif res_type == "qAllDepth":
                await self._handle_all_depth_data(message_data)
            elif res_type == "qDeal":
                await self._handle_deal_data(message_data)
            elif res_type == "qKLine":
                await self._handle_kline_data(message_data)
            elif res_type == "qStats":
                await self._handle_stats_data(message_data)
            elif res_type == "uBalance":
                await self._handle_user_balance_data(message_data)
            elif res_type == "uOrder":
                await self._handle_user_order_data(message_data)
            elif res_type == "uTrade":
                await self._handle_user_trade_data(message_data)
            elif res_type == "znxMessage":
                await self._handle_system_message(message_data)
            else:
                logger.debug(f"Unhandled message type: {res_type}")
                
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
    
    async def _handle_depth_data(self, data: Dict[str, Any]):
        """Handle depth update data."""
        try:
            depth = DepthData(
                id=data.get("id", ""),
                symbol=self.sodex_client._convert_symbol(data.get("s", ""), reverse=True),
                side="BID" if int(data.get("m", 1)) == 1 else "ASK",
                price=float(data.get("p", 0)),
                quantity=float(data.get("q", 0)),
                timestamp=int(data.get("t", 0))
            )
            
            callback_key = f"symbol_{data.get('s', '')}"
            if callback_key in self.callbacks:
                self.callbacks[callback_key](depth)
                
        except Exception as e:
            logger.error(f"Error handling depth data: {e}")
    
    async def _handle_all_depth_data(self, data: Dict[str, Any]):
        """Handle full depth data."""
        try:
            # Convert raw asks and bids data to OBItem objects
            asks = []
            for ask_data in data.get("a", []):
                if len(ask_data) >= 2:
                    asks.append(OBItem(price=float(ask_data[0]), quantity=float(ask_data[1])))
            
            bids = []
            for bid_data in data.get("b", []):
                if len(bid_data) >= 2:
                    bids.append(OBItem(price=float(bid_data[0]), quantity=float(bid_data[1])))
            
            # Create Orderbook instance
            orderbook = Orderbook(
                symbol=self.sodex_client._convert_symbol(data.get("s", ""), reverse=True),
                timestamp=int(data.get("t", 0)) if data.get("t") else int(asyncio.get_event_loop().time() * 1000),
                asks=asks,
                bids=bids
            )
            
            callback_key = f"symbol_{data.get('s', '')}"
            if callback_key in self.callbacks:
                self.callbacks[callback_key](orderbook)
                
        except Exception as e:
            logger.error(f"Error handling all depth data: {e}")
    
    async def _handle_deal_data(self, data: Dict[str, Any]):
        """Handle trade/deal data."""
        try:
            # Convert side integer to string format expected by TradeData
            side_int = int(data.get("m", 0))
            side_str = "BUY" if side_int == 1 else "SELL"
            
            trade = TradeData(
                symbol=self.sodex_client._convert_symbol(data.get("s", ""), reverse=True),
                timestamp=int(data.get("t", 0)),
                price=float(data.get("p", 0)),
                quantity=float(data.get("a", 0)),
                side=side_str
            )
            
            callback_key = f"symbol_{data.get('s', '')}"
            if callback_key in self.callbacks:
                self.callbacks[callback_key](trade)
                
        except Exception as e:
            logger.error(f"Error handling deal data: {e}")
    
    async def _handle_kline_data(self, data: Dict[str, Any]):
        """Handle kline data."""
        try:
            kline = KlineStreamData(
                symbol=self.sodex_client._convert_symbol(data.get("s", ""), reverse=True),
                open_price=float(data.get("o", 0)),
                close_price=float(data.get("c", 0)),
                high_price=float(data.get("h", 0)),
                low_price=float(data.get("l", 0)),
                volume=float(data.get("a", 0)),
                quote_volume=float(data.get("v", 0)),
                interval=data.get("i", ""),
                timestamp=int(data.get("t", 0))
            )
            
            callback_key = f"kline_{data.get('s', '')}_{data.get('i', '')}"
            if callback_key in self.callbacks:
                self.callbacks[callback_key](kline)
                
        except Exception as e:
            logger.error(f"Error handling kline data: {e}")
    
    async def _handle_stats_data(self, data: Dict[str, Any]):
        """Handle statistics data."""
        try:
            stats = TickerData(
                symbol=self.sodex_client._convert_symbol(data.get("s", ""), reverse=True),
                timestamp=int(data.get("t", 0)) if data.get("t") else int(asyncio.get_event_loop().time() * 1000),
                open_price=float(data.get("o", 0)),
                close_price=float(data.get("c", 0)),
                high_price=float(data.get("h", 0)),
                low_price=float(data.get("l", 0)),
                volume=float(data.get("a", 0)),
                quote_volume=float(data.get("v", 0)),
                price_change_percent=float(data.get("r", 0))
            )
            
            if "stats" in self.callbacks:
                self.callbacks["stats"](stats)
                
        except Exception as e:
            logger.error(f"Error handling stats data: {e}")
    
    async def _handle_user_balance_data(self, data: Dict[str, Any]):
        """Handle user balance data."""
        try:
            balance = UserBalanceData(
                coin=data.get("coin", ""),
                balance_type=int(data.get("balanceType", 0)),
                balance=float(data.get("balance", 0)),
                freeze=float(data.get("freeze", 0)),
                available_balance=float(data.get("availableBalance", 0)),
                estimated_total_amount=float(data.get("estimatedTotalAmount", 0)),
                estimated_cny_amount=float(data.get("estimatedCynAmount", 0)),
                estimated_available_amount=float(data.get("estimatedAvailableAmount", 0)),
                estimated_coin_type=data.get("estimatedCoinType", "")
            )
            
            if "user_balance" in self.callbacks:
                self.callbacks["user_balance"](balance)
                
        except Exception as e:
            logger.error(f"Error handling user balance data: {e}")
    
    async def _handle_user_order_data(self, data: Dict[str, Any]):
        """Handle user order data."""
        try:
            order = UserOrderData(
                order_id=str(data.get("orderId", "")),
                balance_type=int(data.get("balanceType", 0)),
                order_type="BUY" if int(data.get("orderType", 1)) == 1 else "SELL",
                symbol=self.sodex_client._convert_symbol(data.get("symbol", ""), reverse=True),
                price=float(data.get("price", 0)),
                direction="BUY" if int(data.get("direction", 1)) == 1 else "SELL",
                orig_qty=float(data.get("origQty", 0)),
                avg_price=float(data.get("avgPrice", 0)),
                executed_qty=float(data.get("dealQty", 0)),
                state=int(data.get("state", 0)),
                create_time=int(data.get("createTime", 0))
            )
            
            if "user_order" in self.callbacks:
                self.callbacks["user_order"](order)
                
        except Exception as e:
            logger.error(f"Error handling user order data: {e}")
    
    async def _handle_user_trade_data(self, data: Dict[str, Any]):
        """Handle user trade data."""
        try:
            trade = UserTradeData(
                order_id=str(data.get("orderId", "")),
                price=float(data.get("price", 0)),
                quantity=float(data.get("quantity", 0)),
                margin_unfrozen=float(data.get("marginUnfrozen", 0)),
                timestamp=int(data.get("timestamp", 0))
            )
            
            if "user_trade" in self.callbacks:
                self.callbacks["user_trade"](trade)
                
        except Exception as e:
            logger.error(f"Error handling user trade data: {e}")
    
    async def _handle_system_message(self, data: Dict[str, Any]):
        """Handle system notification message."""
        try:
            message = SystemMessage(
                id=int(data.get("id", 0)),
                title=data.get("title", ""),
                content=data.get("content", ""),
                agg_type=data.get("aggType", ""),
                detail_type=data.get("detailType", ""),
                created_time=int(data.get("createdTime", 0)),
                all_scope=bool(data.get("allScope", False)),
                user_id=int(data.get("userId", 0)),
                read=bool(data.get("read", False))
            )
            
            logger.info(f"System message: {message.title} - {message.content}")
            
        except Exception as e:
            logger.error(f"Error handling system message: {e}")
    
    async def _handle_reconnect(self):
        """Handle WebSocket reconnection."""
        if self.reconnect_count >= self.config.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached, giving up")
            return
        
        self.reconnect_count += 1
        logger.info(f"Attempting to reconnect ({self.reconnect_count}/{self.config.max_reconnect_attempts})")
        
        await asyncio.sleep(self.config.reconnect_interval)
        
        if await self.connect():
            # Re-authenticate if needed
            if self.auth_token:
                await self.authenticate()
            
            # Resubscribe to all previous subscriptions
            await self._resubscribe()
            
            # Restart listening
            await self.start_listening()
        else:
            await self._handle_reconnect()
    
    async def _resubscribe(self):
        """Resubscribe to all previous subscriptions after reconnection."""
        logger.info("Resubscribing to previous subscriptions")
        
        # This is a simplified resubscription - in a production system,
        # you would want to store subscription details and recreate them
        for subscription in self.subscriptions:
            logger.debug(f"Would resubscribe to: {subscription}")
        
        # Note: Actual resubscription would require storing subscription parameters
        # and recreating the subscription messages
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get WebSocket connection status.
        
        Returns:
            Dictionary with connection status information
        """
        return {
            'connected': self.is_connected,
            'authenticated': self.is_authenticated,
            'subscriptions': len(self.subscriptions),
            'reconnect_count': self.reconnect_count,
            'websocket_url': self.url
        } 