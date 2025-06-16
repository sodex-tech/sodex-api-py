import asyncio
from datetime import datetime

from sodex_api import SodexClient, SodexAPIError, SodexWebSocketClient, UserOrderData, Config

class OrderManager:
    def __init__(self):
        self.client = SodexClient()
        self.ws_client = SodexWebSocketClient(host=Config.SODEX_WS_URL)
        self.placed_order_id = None
        self.order_received = False
        
    def handle_order_data(self, data: UserOrderData):
        timestamp = datetime.now().strftime('%H:%M:%S')
        state_map = {1: "NEW", 2: "PARTIAL", 3: "FILLED", 4: "CANCELLED"}
        direction_map = {1: "BUY", 2: "SELL"}
        
        state_str = state_map.get(data.state, f"UNKNOWN({data.state})")
        direction_str = direction_map.get(data.direction, f"UNKNOWN({data.direction})")
        
        print(f"[{timestamp}] Order Update - ID:{data.order_id} {data.symbol} {direction_str} {data.orig_qty}@{data.price} State:{state_str}")
        
        if data.order_id == self.placed_order_id:
            self.order_received = True
            print(f"[{timestamp}] Received order data for placed order: {data.order_id}")

    async def run(self):
        try:
            print("Connecting to WebSocket...")
            if not await self.ws_client.connect():
                print("Failed to connect to WebSocket")
                return
            
            print("Authenticating WebSocket...")
            if not await self.ws_client.authenticate():
                print("Failed to authenticate WebSocket")
                return
            
            print("Subscribing to user order data...")
            await self.ws_client.subscribe_user_data(order_callback=self.handle_order_data)
            
            await self.ws_client.start_listening()
            
            symbol = "BTCUSDT"
            side = "BUY"
            order_type = "LIMIT"
            price = 100000.0
            quantity = 0.0001
            
            print(f"Placing order: {side} {quantity} {symbol} at {price}")
            
            self.placed_order_id = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                price=price,
                quantity=quantity
            )
            
            if self.placed_order_id:
                print(f"Order placed successfully. Order ID: {self.placed_order_id}")
                
                print("Waiting for order data from WebSocket...")
                timeout = 30
                elapsed = 0
                while not self.order_received and elapsed < timeout:
                    await asyncio.sleep(1)
                    elapsed += 1
                
                if self.order_received:
                    print("Order data received via WebSocket, proceeding to cancel...")
                    
                    cancel_result = self.client.cancel_order(symbol, self.placed_order_id)
                    if cancel_result:
                        print(f"Order cancelled successfully: {cancel_result}")
                    else:
                        print("Failed to cancel order")
                else:
                    print("Timeout waiting for order data from WebSocket")
            else:
                print("Failed to place order")
                
        except SodexAPIError as e:
            print(f"API error: {e}")
        except Exception as e:
            print(f"Unknown error: {e}")
        finally:
            await self.ws_client.disconnect()
            print("Disconnected from WebSocket")

async def main():
    order_manager = OrderManager()
    await order_manager.run()

if __name__ == "__main__":
    asyncio.run(main()) 