"""SoDEX API Python Client.

A Python client library for interacting with the SoDEX API.
Supports both spot and futures trading.
"""

__version__ = "2.0.0"

# Legacy imports for backward compatibility
from .client import SodexClient
from .ws_client import SodexWebSocketClient
from .exceptions import SodexAPIError
from .models import *
from .config import Config

# New modular imports
from .spot import SpotClient
from .futures import FuturesClient
from .core import (
    BaseClient,
    BaseWebSocketClient,
    Authenticator,
    AuthenticationError,
    RateLimitError,
    InvalidOrderError,
    InsufficientBalanceError,
    MarketDataError,
    WebSocketError
)

__all__ = [
    # Legacy exports
    "SodexClient",
    "SodexWebSocketClient",
    "SodexAPIError",
    # New modular exports
    "SpotClient",
    "FuturesClient",
    # Core components
    "BaseClient",
    "BaseWebSocketClient",
    "Authenticator",
    "Config",
    # Exceptions
    "AuthenticationError",
    "RateLimitError",
    "InvalidOrderError",
    "InsufficientBalanceError",
    "MarketDataError",
    "WebSocketError",
    # Version
    "__version__",
] 