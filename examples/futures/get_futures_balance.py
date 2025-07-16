"""Example: Get futures account balance."""

from sodex_api import FuturesClient, Config
from loguru import logger


def main():
    """Get and display futures account balances."""
    # Initialize the futures client
    client = FuturesClient(
        api_key=Config.SODEX_API_KEY,
        secret_key=Config.SODEX_SECRET_KEY,
        base_url=Config.SODEX_FUTURES_BASE_URL
    )
    
    try:
        # Get all futures balances
        balances = client.get_balances()
        
        if not balances:
            logger.info("No futures balances found")
            return
        
        logger.info(f"Found {len(balances)} futures balance(s):")
        
        for balance in balances:
            logger.info(f"\nCoin: {balance.coin}")
            logger.info(f"  Balance Type: {balance.balance_type}")
            logger.info(f"  Wallet Balance: {balance.wallet_balance}")
            logger.info(f"  Available Balance: {balance.available_balance}")
            logger.info(f"  Open Order Margin Frozen: {balance.open_order_margin_frozen}")
            logger.info(f"  Isolated Margin: {balance.isolated_margin}")
            logger.info(f"  Crossed Margin: {balance.crossed_margin}")
            logger.info(f"  Bonus: {balance.bonus}")
            
    except Exception as e:
        logger.error(f"Error getting futures balances: {e}")


if __name__ == "__main__":
    main()