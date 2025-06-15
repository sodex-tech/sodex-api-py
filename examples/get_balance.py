from sodex_api.client import SodexClient, SodexAPIError

def main():
    try:
        client = SodexClient()
        
        print("Getting all account balances...")
        balances = client.get_account_balances()
        
        if balances:
            print(f"Found {len(balances)} assets:")
            print("-" * 50)
            for balance in balances:
                total = balance.available + balance.locked
                if total > 0:
                    print(f"{balance.symbol:10} | Available: {balance.available:15.8f} | Locked: {balance.locked:15.8f} | Total: {total:15.8f}")
        else:
            print("No balances found")
        
        print("\nGetting specific coin balance (BTC)...")
        btc_balance = client.get_account_balance("BTC")
        
        if btc_balance:
            total_btc = btc_balance.available + btc_balance.locked
            print(f"BTC Balance - Available: {btc_balance.available:.8f}, Locked: {btc_balance.locked:.8f}, Total: {total_btc:.8f}")
        else:
            print("BTC balance not found")
            
    except SodexAPIError as e:
        print(f"API error: {e}")
    except Exception as e:
        print(f"Unknown error: {e}")

if __name__ == "__main__":
    main() 