from datetime import datetime

from sodex_api import SodexClient, SodexAPIError

def main():
    try:
        client = SodexClient()
        
        server_time = client.get_server_time()
        
        server_datetime = datetime.fromtimestamp(server_time / 1000)
        
        print(f"Server time: {server_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        
    except SodexAPIError as e:
        print(f"API error: {e}")
    except Exception as e:
        print(f"Unknown error: {e}")

if __name__ == "__main__":
    main() 