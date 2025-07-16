"""Legacy WebSocket client module for backward compatibility."""

from .spot.ws_client import SpotWebSocketClient, WebSocketConfig, SubscriptionType

# Create alias for backward compatibility
SodexWebSocketClient = SpotWebSocketClient

__all__ = ['SodexWebSocketClient', 'WebSocketConfig', 'SubscriptionType'] 