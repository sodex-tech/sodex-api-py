#!/usr/bin/env python3
"""
Example: Get Symbol List

This example demonstrates how to retrieve the list of all available trading symbols
and their configuration details from the Sodex exchange.
"""

from loguru import logger

from sodex_api.spot import SpotClient


def main():
    """Main function to demonstrate getting symbol list."""
    try:
        # Initialize the Sodex client
        client = SpotClient()
        
        # Get the list of all trading symbols
        logger.info("Fetching symbol list...")
        symbols = client.get_symbol_list()
        
        if not symbols:
            logger.warning("No symbols found")
            return
        
        logger.info(f"Found {len(symbols)} trading symbols")
        
        # Display information about each symbol
        print("\n" + "="*80)
        print("TRADING SYMBOLS")
        print("="*80)
        
        for symbol in symbols:
            print(f"\nSymbol: {symbol.symbol}")
            print(f"  ID: {symbol.id}")
            print(f"  Trading Enabled: {symbol.is_active}")
            print(f"  Base Coin: {symbol.sell_coin}")
            print(f"  Quote Coin: {symbol.buy_coin}")
            print(f"  Price Precision: {symbol.price_precision}")
            print(f"  Quantity Precision: {symbol.quantity_precision}")
            print(f"  Min Quantity: {symbol.min_quantity}")
            print(f"  Maker Fee: {symbol.maker_fee_rate}%")
            print(f"  Taker Fee: {symbol.taker_fee_rate}%")
            print(f"  Supported Order Types: {', '.join(symbol.supported_order_types)}")
            print(f"  Hot Symbol: {symbol.hot}")
        
        # Show some statistics
        print("\n" + "="*80)
        print("STATISTICS")
        print("="*80)
        
        active_symbols = [s for s in symbols if s.is_active]
        hot_symbols = [s for s in symbols if s.hot]
        
        print(f"Total Symbols: {len(symbols)}")
        print(f"Active Symbols: {len(active_symbols)}")
        print(f"Hot Symbols: {len(hot_symbols)}")
        
        # Show unique base and quote coins
        base_coins = set(s.sell_coin for s in symbols)
        quote_coins = set(s.buy_coin for s in symbols)
        
        print(f"Unique Base Coins: {len(base_coins)} ({', '.join(sorted(base_coins))})")
        print(f"Unique Quote Coins: {len(quote_coins)} ({', '.join(sorted(quote_coins))})")
        
    except Exception as e:
        logger.error(f"Error getting symbol list: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 