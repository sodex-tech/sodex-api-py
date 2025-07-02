import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SODEX_API_KEY = os.getenv("SODEX_API_KEY", "1234567890")
    SODEX_SECRET_KEY = os.getenv("SODEX_SECRET_KEY", "1234567890")
    SODEX_BASE_URL = 'http://gateway-jp.test.sodex.dev'
    SODEX_WS_URL = 'ws://gateway-jp.test.sodex.dev'
    SODEX_BASE_URL_EXT = 'http://gateway-jp.test.sodex.dev'
