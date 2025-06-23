import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SODEX_API_KEY = os.getenv("SODEX_API_KEY", "1234567890")
    SODEX_SECRET_KEY = os.getenv("SODEX_SECRET_KEY", "1234567890")
    SODEX_BASE_URL = 'https://sodex-openapi.sosovalue.io'
    SODEX_WS_URL = 'wss://sodex-openapi.sosovalue.io'
    SODEX_BASE_URL_EXT = 'https://test-vex.sosovalue.io'
