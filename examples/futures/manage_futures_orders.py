"""Example: Manage futures orders (place, query, cancel)."""

from sodex_api import FuturesClient, Config
from loguru import logger
import time


def main():
    """Comprehensive futures order management example."""
    # Initialize the futures client
    client = FuturesClient(
        api_key=Config.SODEX_API_KEY,
        secret_key=Config.SODEX_SECRET_KEY,
        base_url=Config.SODEX_FUTURES_BASE_URL
    )
    
    try:
        symbol = "btc_usdt"
        
        # 1. Place multiple orders
        logger.info("=== Placing Multiple Futures Orders ===")
        order_ids = []
        
        # Place buy orders at different prices
        for i, price in enumerate([69000, 69500, 70000]):
            order_id = client.place_order(
                symbol=symbol,
                order_side="BUY",
                order_type="LIMIT",
                position_side="LONG",
                quantity=100,
                price=price,
                leverage=5,
                client_order_id=f"test_order_{i+1}"
            )
            if order_id:
                order_ids.append(order_id)
                logger.success(f"Placed buy order at ${price}: {order_id}")
            time.sleep(0.5)  # Avoid rate limiting
        
        # 2. Query open orders
        logger.info("\n=== Querying Open Orders ===")
        orders_response = client.get_orders(
            symbol=symbol,
            state="UNFINISHED",
            page=1,
            size=20
        )
        
        open_orders = orders_response.get('items', [])
        logger.info(f"Found {len(open_orders)} open orders")
        
        for order in open_orders[:5]:  # Show first 5
            logger.info(f"Order {order.order_id}:")
            logger.info(f"  Side: {order.order_side}, Position: {order.position_side}")
            logger.info(f"  Price: {order.price}, Quantity: {order.orig_qty}")
            logger.info(f"  Status: {order.state}, Executed: {order.executed_qty}")
        
        # 3. Get order fills
        logger.info("\n=== Checking Order Fills ===")
        fills_response = client.get_order_fills(
            symbol=symbol,
            page=1,
            size=10
        )
        
        fills = fills_response.get('items', [])
        if fills:
            logger.info(f"Found {len(fills)} order fills")
            for fill in fills[:3]:
                logger.info(f"Fill {fill.exec_id}: {fill.quantity} @ ${fill.price}")
        else:
            logger.info("No fills found yet")
        
        # 4. Cancel specific order
        if order_ids:
            logger.info("\n=== Canceling Single Order ===")
            cancel_id = order_ids[0]
            cancelled = client.cancel_order(cancel_id)
            if cancelled:
                logger.success(f"Successfully cancelled order: {cancel_id}")
        
        # 5. Batch cancel remaining orders
        if len(order_ids) > 1:
            logger.info("\n=== Batch Canceling Orders ===")
            remaining_ids = order_ids[1:]
            results = client.batch_cancel_orders(remaining_ids)
            logger.info(f"Batch cancel results: {len(results)} orders processed")
        
        # 6. Query order history
        logger.info("\n=== Querying Order History ===")
        history_response = client.get_orders(
            symbol=symbol,
            state="HISTORY",
            page=1,
            size=5
        )
        
        history = history_response.get('items', [])
        logger.info(f"Found {history_response.get('total', 0)} historical orders")
        for order in history:
            logger.info(f"Historical order {order.order_id}: {order.state}")
            
    except Exception as e:
        logger.error(f"Error in futures order management: {e}")


if __name__ == "__main__":
    main()