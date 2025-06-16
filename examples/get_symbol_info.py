from datetime import datetime

from sodex_api import SodexClient, SodexAPIError

def main():
    try:
        client = SodexClient()
        
        symbol = "BTCUSDT"
        
        print(f"Getting symbol information for {symbol}...")
        print("=" * 60)
        
        ticker = client.get_ticker(symbol)
        if ticker:
            print(f"24hr Ticker Statistics:")
            print(f"  Symbol: {ticker.symbol}")
            print(f"  Current Price: {ticker.close_price:.2f}")
            print(f"  Open Price: {ticker.open_price:.2f}")
            print(f"  High Price: {ticker.high_price:.2f}")
            print(f"  Low Price: {ticker.low_price:.2f}")
            print(f"  Volume: {ticker.volume:.4f}")
            print(f"  Quote Volume: {ticker.quote_volume:.2f}")
            print(f"  Price Change: {ticker.price_change_percent:.2f}%")
            print(f"  Timestamp: {datetime.fromtimestamp(ticker.timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"No ticker data found for {symbol}")
        
        print("\n" + "-" * 60)
        
        print(f"Getting orderbook for {symbol}...")
        orderbook = client.get_orderbook(symbol, limit=5)
        if orderbook:
            print(f"Orderbook (Top 5):")
            print(f"  Symbol: {orderbook.symbol}")
            print(f"  Asks (Sell Orders):")
            for ask in orderbook.asks[:5]:
                print(f"    Price: {ask.price:.2f}, Quantity: {ask.quantity:.6f}")
            print(f"  Bids (Buy Orders):")
            for bid in orderbook.bids[:5]:
                print(f"    Price: {bid.price:.2f}, Quantity: {bid.quantity:.6f}")
        else:
            print(f"No orderbook data found for {symbol}")
        
        print("\n" + "-" * 60)
        
        print(f"Getting recent trades for {symbol}...")
        trades = client.get_recent_trades(symbol, limit=5)
        if trades:
            print(f"Recent Trades (Last 5):")
            for trade in trades:
                trade_time = datetime.fromtimestamp(trade.timestamp / 1000).strftime('%H:%M:%S')
                print(f"  [{trade_time}] {trade.side} {trade.quantity:.6f} @ {trade.price:.2f}")
        else:
            print(f"No recent trades found for {symbol}")
        
        print("\n" + "=" * 60)
        print("Getting all tickers summary...")
        
        all_tickers = client.get_all_tickers()
        if all_tickers:
            print(f"Found {len(all_tickers)} trading pairs:")
            print(f"{'Symbol':<12} {'Price':<12} {'Change%':<10} {'Volume':<15}")
            print("-" * 50)
            for ticker in all_tickers[:10]:
                print(f"{ticker.symbol:<12} {ticker.close_price:<12.2f} {ticker.price_change_percent:<10.2f} {ticker.volume:<15.4f}")
            if len(all_tickers) > 10:
                print(f"... and {len(all_tickers) - 10} more pairs")
        else:
            print("No ticker data found")
            
    except SodexAPIError as e:
        print(f"API error: {e}")
    except Exception as e:
        print(f"Unknown error: {e}")

if __name__ == "__main__":
    main() 