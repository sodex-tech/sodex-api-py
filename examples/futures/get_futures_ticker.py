"""Example: Get futures ticker information."""

from sodex_api import FuturesClient, Config
from loguru import logger


def main():
    """Get and display futures ticker information."""
    # Initialize the futures client
    client = FuturesClient(
        api_key=Config.SODEX_API_KEY,
        secret_key=Config.SODEX_SECRET_KEY,
        base_url=Config.SODEX_FUTURES_BASE_URL
    )
    
    try:
        # Get ticker for a specific symbol
        symbol = "BTC_USDC"
        ticker = client.get_ticker(symbol)
        
        logger.info(f"Ticker information for {symbol}:")
        logger.info(f"  Current Price: {ticker.close_price}")
        logger.info(f"  24h Change: {ticker.price_change_percent}%")
        logger.info(f"  24h High: {ticker.high_price}")
        logger.info(f"  24h Low: {ticker.low_price}")
        logger.info(f"  24h Volume: {ticker.volume}")
        logger.info(f"  24h Quote Volume: {ticker.quote_volume}")
        
        # Get all tickers
        logger.info("\nGetting all futures tickers...")
        all_tickers = client.get_all_tickers()
        
        logger.info(f"Found {len(all_tickers)} futures tickers:")
        for ticker in all_tickers[:5]:  # Show first 5
            logger.info(f"  {ticker.symbol}: ${ticker.close_price} ({ticker.price_change_percent:+.2f}%)")
            
    except Exception as e:
        logger.error(f"Error getting futures ticker: {e}")


if __name__ == "__main__":
    main()