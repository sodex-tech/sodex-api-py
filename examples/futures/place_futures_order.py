"""Example: Place a futures order."""

from sodex_api import FuturesClient, Config
from loguru import logger


def main():
    """Place a futures limit order example."""
    # Initialize the futures client
    client = FuturesClient(
        api_key=Config.SODEX_API_KEY,
        secret_key=Config.SODEX_SECRET_KEY,
        base_url=Config.SODEX_FUTURES_BASE_URL
    )
    
    try:
        # Example: Place a limit buy order for BTC futures
        symbol = "btc_usdt"
        order_side = "BUY"
        order_type = "LIMIT"
        position_side = "LONG"  # Open long position
        quantity = 100  # Contract quantity
        price = 70000.0  # Limit price
        leverage = 10  # 10x leverage
        
        logger.info(f"Placing {order_side} {order_type} order for {symbol}")
        logger.info(f"Position Side: {position_side}, Quantity: {quantity}, Price: {price}, Leverage: {leverage}x")
        
        # Place the order
        order_id = client.place_order(
            symbol=symbol,
            order_side=order_side,
            order_type=order_type,
            position_side=position_side,
            quantity=quantity,
            price=price,
            leverage=leverage,
            time_in_force="GTC"  # Good Till Cancel
        )
        
        if order_id:
            logger.success(f"Order placed successfully! Order ID: {order_id}")
            
            # Get order details
            order_detail = client.get_order_detail(order_id)
            logger.info(f"Order Status: {order_detail.state}")
            logger.info(f"Order Type: {order_detail.order_type}")
            logger.info(f"Price: {order_detail.price}")
            logger.info(f"Quantity: {order_detail.orig_qty}")
            logger.info(f"Executed Quantity: {order_detail.executed_qty}")
            logger.info(f"Margin Frozen: {order_detail.margin_frozen}")
        else:
            logger.error("Failed to place order")
            
    except Exception as e:
        logger.error(f"Error placing futures order: {e}")


if __name__ == "__main__":
    main()