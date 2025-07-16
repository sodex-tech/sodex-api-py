import time
from typing import List
from loguru import logger

from sodex_api.spot import SpotClient
from sodex_api.models import Order, OrderSide

class BatchTrader:
    def __init__(self):
        self.client = SpotClient()
        
    def create_ladder_orders(self, symbol: str, side: OrderSide, base_price: float, 
                           levels: int, price_step: float, quantity: float) -> List[Order]:
        orders = []
        for i in range(levels):
            if side == "BUY":
                price = base_price * (1 - (i + 1) * price_step)
            else:
                price = base_price * (1 + (i + 1) * price_step)
            
            order = Order(
                order_id="",
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                type="LIMIT",
                status="NEW",
                timestamp=int(time.time() * 1000)
            )
            orders.append(order)
        return orders
    
    def grid_trading_strategy(self, symbol: str):
        logger.info(f"Starting grid trading for {symbol}")
        
        ticker = self.client.get_ticker(symbol)
        current_price = ticker.close_price
        logger.info(f"Current price: {current_price}")
        
        buy_orders = self.create_ladder_orders(
            symbol=symbol,
            side="BUY",
            base_price=current_price,
            levels=3,
            price_step=0.01,
            quantity=0.001
        )
        
        sell_orders = self.create_ladder_orders(
            symbol=symbol,
            side="SELL",
            base_price=current_price,
            levels=3,
            price_step=0.01,
            quantity=0.001
        )
        
        all_orders = buy_orders + sell_orders
        
        logger.info(f"Placing {len(all_orders)} grid orders")
        order_ids = self.client.batch_place_orders(all_orders)
        logger.info(f"Grid orders placed: {order_ids}")
        
        return order_ids
    
    def scalping_strategy(self, symbol: str):
        logger.info(f"Starting scalping strategy for {symbol}")
        
        ticker = self.client.get_ticker(symbol)
        current_price = ticker.close_price
        
        orders = []
        
        tight_buy = Order(
            order_id="",
            symbol=symbol,
            side="BUY",
            quantity=0.002,
            price=current_price * 0.999,
            type="LIMIT",
            status="NEW",
            timestamp=int(time.time() * 1000)
        )
        
        tight_sell = Order(
            order_id="",
            symbol=symbol,
            side="SELL",
            quantity=0.002,
            price=current_price * 1.001,
            type="LIMIT",
            status="NEW",
            timestamp=int(time.time() * 1000)
        )
        
        orders.extend([tight_buy, tight_sell])
        
        logger.info("Placing scalping orders")
        order_ids = self.client.batch_place_orders(orders)
        logger.info(f"Scalping orders placed: {order_ids}")
        
        return order_ids
    
    def cancel_all_orders(self, symbol: str):
        logger.info(f"Cancelling all orders for {symbol}")
        cancelled = self.client.cancel_all_orders(symbol)
        logger.info(f"Cancelled {len(cancelled)} orders")
        return cancelled


def main():
    trader = BatchTrader()
    symbol = "BTCUSDT"
    
    try:
        grid_order_ids = trader.grid_trading_strategy(symbol)
        
        time.sleep(3)
        
        scalp_order_ids = trader.scalping_strategy(symbol)
        
        time.sleep(2)
        
        open_orders = trader.client.get_open_orders(symbol)
        logger.info(f"Total open orders: {len(open_orders)}")
        
        for order in open_orders:
            logger.info(f"Order: {order.side} {order.quantity} @ {order.price}")
        
        time.sleep(2)
        
        trader.cancel_all_orders(symbol)
        
        final_orders = trader.client.get_open_orders(symbol)
        logger.info(f"Remaining orders: {len(final_orders)}")
        
        logger.info("Advanced batch trading completed")
        
    except Exception as e:
        logger.error(f"Error in batch trading: {e}")
        trader.cancel_all_orders(symbol)


if __name__ == "__main__":
    main() 