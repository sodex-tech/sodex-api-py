"""Example: Get futures orderbook."""

from sodex_api import FuturesClient, Config
from loguru import logger


def main():
    """Get and display futures orderbook."""
    # Initialize the futures client
    client = FuturesClient(
        api_key=Config.SODEX_API_KEY,
        secret_key=Config.SODEX_SECRET_KEY,
        base_url=Config.SODEX_FUTURES_BASE_URL
    )
    
    try:
        # Get orderbook for BTC futures
        symbol = "BTC_USDC"
        level = 10  # Get top 10 levels
        
        orderbook = client.get_orderbook(symbol, level)
        
        logger.info(f"Orderbook for {symbol}:")
        logger.info(f"Update ID: {orderbook.update_id}")
        logger.info(f"Timestamp: {orderbook.timestamp}")
        
        # Display top 5 asks
        logger.info("\nTop 5 Asks (Sell Orders):")
        for i, ask in enumerate(orderbook.asks[:5]):
            logger.info(f"  Level {i+1}: Price: ${ask[0]:.2f}, Quantity: {ask[1]}")
        
        # Display spread
        if orderbook.bids and orderbook.asks:
            spread = orderbook.asks[0][0] - orderbook.bids[0][0]
            spread_percent = (spread / orderbook.bids[0][0]) * 100
            logger.info(f"\nSpread: ${spread:.2f} ({spread_percent:.3f}%)")
        
        # Display top 5 bids
        logger.info("\nTop 5 Bids (Buy Orders):")
        for i, bid in enumerate(orderbook.bids[:5]):
            logger.info(f"  Level {i+1}: Price: ${bid[0]:.2f}, Quantity: {bid[1]}")
            
    except Exception as e:
        logger.error(f"Error getting futures orderbook: {e}")


if __name__ == "__main__":
    main()