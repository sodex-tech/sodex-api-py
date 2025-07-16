"""Core components shared between spot and futures trading."""

from .base import BaseClient, BaseWebSocketClient
from .auth import Authenticator
from .exceptions import (
    SodexAPIError,
    AuthenticationError,
    RateLimitError,
    InvalidOrderError,
    InsufficientBalanceError,
    MarketDataError,
    WebSocketError
)

__all__ = [
    'BaseClient',
    'BaseWebSocketClient',
    'Authenticator',
    'SodexAPIError',
    'AuthenticationError',
    'RateLimitError',
    'InvalidOrderError',
    'InsufficientBalanceError',
    'MarketDataError',
    'WebSocketError'
]