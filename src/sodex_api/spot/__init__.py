"""Spot trading module for Sodex API."""

from .client import SpotClient
from .ws_client import SpotWebSocketClient, WebSocketConfig, SubscriptionType
from .models import (
    Balance,
    Order,
    Orderbook,
    OBItem,
    KlineData,
    TickerData,
    TradeData,
    OrderFill,
    SymbolInfo,
    OrderSide,
    OrderType,
    OrderState,
    DepthData,
    KlineStreamData,
    UserBalanceData,
    UserOrderData,
    UserTradeData,
    SystemMessage
)

__all__ = [
    'SpotClient',
    'SpotWebSocketClient',
    'WebSocketConfig',
    'SubscriptionType',
    'Balance',
    'Order',
    'Orderbook',
    'OBItem',
    'KlineData',
    'TickerData',
    'TradeData',
    'OrderFill',
    'SymbolInfo',
    'OrderSide',
    'OrderType',
    'OrderState',
    'DepthData',
    'KlineStreamData',
    'UserBalanceData',
    'UserOrderData',
    'UserTradeData',
    'SystemMessage'
]