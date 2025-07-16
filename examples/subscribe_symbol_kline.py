import asyncio
from datetime import datetime

from sodex_api.spot import SpotWebSocketClient
from sodex_api.models import DepthData, Orderbook, TradeData
from sodex_api.exceptions import SodexAPIError
from sodex_api.config import Config

def handle_symbol_data(data):
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    if isinstance(data, DepthData):
        side_str = "BUY" if data.side == 1 else "SELL"
        print(f"[{timestamp}] Depth Update - {data.symbol}: {side_str} {data.quantity} @ {data.price}")
    
    elif isinstance(data, Orderbook):
        print(f"[{timestamp}] Full Depth - {data.symbol}:")
        print(f"  Best Ask: {data.asks[0] if data.asks else 'N/A'}")
        print(f"  Best Bid: {data.bids[0] if data.bids else 'N/A'}")
    
    elif isinstance(data, TradeData):
        side_str = "BUY" if data.side == 1 else "SELL"
        print(f"[{timestamp}] Trade - {data.symbol}: {side_str} {data.quantity} @ {data.price}")

def handle_kline_data(data):
    timestamp = datetime.now().strftime('%H:%M:%S')
    change_percent = ((data.close_price - data.open_price) / data.open_price) * 100 if data.open_price > 0 else 0
    print(f"[{timestamp}] Kline - {data.symbol} ({data.interval}): O:{data.open_price} H:{data.high_price} L:{data.low_price} C:{data.close_price} V:{data.volume} Change:{change_percent:.2f}%")

async def main():
    ws_client = SpotWebSocketClient(host=Config.SODEX_WS_URL)
    
    try:
        print("Connecting to WebSocket...")
        if not await ws_client.connect():
            print("Failed to connect to WebSocket")
            return
        
        print("Connected successfully!")
        
        symbol = "BTCUSDT"
        interval = "1m"
        
        print(f"Subscribing to symbol data for {symbol}...")
        await ws_client.subscribe_symbol(symbol, handle_symbol_data)
        
        print(f"Subscribing to kline data for {symbol} with {interval} interval...")
        await ws_client.subscribe_kline(symbol, interval, handle_kline_data)
        
        await ws_client.start_listening()
        
        print(f"Listening for {symbol} symbol and kline data... Press Ctrl+C to stop")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")
    
    except SodexAPIError as e:
        print(f"API error: {e}")
    except Exception as e:
        print(f"Unknown error: {e}")
    finally:
        await ws_client.disconnect()
        print("Disconnected from WebSocket")

if __name__ == "__main__":
    asyncio.run(main()) 