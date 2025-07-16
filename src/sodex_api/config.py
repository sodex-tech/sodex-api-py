import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration settings from environment variables"""
    
    # API Keys
    SODEX_API_KEY = os.getenv("SODEX_API_KEY", "1234567890")
    SODEX_SECRET_KEY = os.getenv("SODEX_SECRET_KEY", "1234567890")
    
    # Base URL
    BASE_URL = os.getenv("SODEX_BASE_URL", "http://gateway-jp.test.sodex.dev")
    
    # Spot Trading URLs
    SODEX_SPOT_BASE_URL = os.getenv("SODEX_SPOT_BASE_URL", BASE_URL)
    SODEX_SPOT_BASE_URL_EXT = os.getenv("SODEX_SPOT_BASE_URL_EXT", BASE_URL)
    SODEX_SPOT_WS_URL = os.getenv("SODEX_SPOT_WS_URL", BASE_URL.replace("http://", "ws://"))
    SODEX_SPOT_WS_URL_EXT = os.getenv("SODEX_SPOT_WS_URL_EXT", BASE_URL.replace("http://", "ws://"))
    
    # Futures Trading URLs
    SODEX_FUTURES_BASE_URL = os.getenv("SODEX_FUTURES_BASE_URL", "http://tiger-gateway-jp.test.sodex.dev")
    SODEX_FUTURES_WS_URL = os.getenv("SODEX_FUTURES_WS_URL", BASE_URL.replace("http://", "ws://"))
    
    # Legacy aliases for backward compatibility
    SODEX_BASE_URL = SODEX_SPOT_BASE_URL
    SODEX_BASE_URL_EXT = SODEX_SPOT_BASE_URL_EXT
    SODEX_WS_URL = SODEX_SPOT_WS_URL
    SODEX_WS_URL_EXT = SODEX_SPOT_WS_URL_EXT
