import time
from loguru import logger

from sodex_api.client import SodexClient
from sodex_api.models import Order, OrderSide


def main():
    client = SodexClient()
    symbol = "BTCUSDT"
    
    logger.info("Getting current market price")
    ticker = client.get_ticker(symbol)
    current_price = ticker.close_price
    logger.info(f"Current price: {current_price}")
    
    orders = []
    
    buy_price = round(current_price * 0.95, 4)
    sell_price = round(current_price * 1.05, 4)
    
    buy_order = Order(
        order_id="",
        symbol=symbol,
        side="BUY",
        quantity=0.0001,
        price=buy_price,
        type="LIMIT",
        status="NEW",
        timestamp=int(time.time() * 1000)
    )
    
    sell_order = Order(
        order_id="",
        symbol=symbol,
        side="SELL",
        quantity=0.0001,
        price=sell_price,
        type="LIMIT",
        status="NEW",
        timestamp=int(time.time() * 1000)
    )
    
    orders.extend([buy_order, sell_order])
    
    logger.info("Placing batch orders")
    order_ids = client.batch_place_orders(orders)
    logger.info(f"Placed orders: {order_ids}")
    
    time.sleep(2)
    
    open_orders = client.get_open_orders(symbol)
    logger.info(f"Open orders: {len(open_orders)}")
    
    logger.info("Cancelling batch orders")
    cancelled = client.cancel_orders_by_ids(order_ids)
    logger.info(f"Cancelled orders: {cancelled}")
    
    logger.info("Batch trading completed")


if __name__ == "__main__":
    main() 