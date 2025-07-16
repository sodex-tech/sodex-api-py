"""Enhanced exception hierarchy for Sodex API."""


class SodexAPIError(Exception):
    """Base exception for all Sodex API errors."""
    
    def __init__(self, message: str, code: int = -1, response_data: dict = None):
        super().__init__(message)
        self.code = code
        self.response_data = response_data or {}


class AuthenticationError(SodexAPIError):
    """Raised when authentication fails."""
    pass


class RateLimitError(SodexAPIError):
    """Raised when API rate limit is exceeded."""
    pass


class InvalidOrderError(SodexAPIError):
    """Raised when order parameters are invalid."""
    pass


class InsufficientBalanceError(SodexAPIError):
    """Raised when account has insufficient balance."""
    pass


class MarketDataError(SodexAPIError):
    """Raised when market data request fails."""
    pass


class WebSocketError(SodexAPIError):
    """Raised for WebSocket-related errors."""
    pass


class NetworkError(SodexAPIError):
    """Raised for network-related issues."""
    pass


class SignatureError(AuthenticationError):
    """Raised when signature generation or validation fails."""
    pass