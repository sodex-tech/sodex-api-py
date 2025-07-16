# Sodex API - Futures Trading

This document describes the futures trading functionality in the Sodex API Python client.

## New Directory Structure

The codebase has been reorganized for better modularity and separation of concerns:

```
src/sodex_api/
├── core/                   # Shared core components
│   ├── __init__.py
│   ├── auth.py            # Authentication handling
│   ├── base.py            # Base classes for clients
│   └── exceptions.py      # Enhanced exception hierarchy
├── spot/                   # Spot trading module
│   ├── __init__.py
│   ├── client.py          # Spot trading client
│   └── models.py          # Spot trading models
├── futures/                # Futures trading module
│   ├── __init__.py
│   ├── client.py          # Futures trading client
│   └── models.py          # Futures trading models
├── client.py              # Legacy spot client (backward compatibility)
├── models.py              # Legacy models (backward compatibility)
├── ws_client.py           # WebSocket client
├── config.py              # Configuration with futures support
└── __init__.py            # Main package exports
```

## Installation

```bash
pip install -e .
```

## Configuration

The configuration now supports separate URLs for spot and futures trading:

```python
from sodex_api import Config

# Futures-specific configuration
Config.SODEX_FUTURES_BASE_URL  # Futures REST API base URL
Config.SODEX_FUTURES_WS_URL    # Futures WebSocket URL
```

## Basic Usage

### Initialize Futures Client

```python
from sodex_api import FuturesClient, Config

# Create futures client
client = FuturesClient(
    api_key=Config.SODEX_API_KEY,
    secret_key=Config.SODEX_SECRET_KEY,
    base_url=Config.SODEX_FUTURES_BASE_URL
)
```

### Public Market Data (No Authentication Required)

```python
# Get server time
server_time = client.get_server_time()

# Get symbol details
symbol_info = client.get_symbol_detail("btc_usdc")

# Get ticker
ticker = client.get_ticker("BTC_USDC")

# Get all tickers
all_tickers = client.get_all_tickers()

# Get orderbook
orderbook = client.get_orderbook("BTC_USDC", level=20)

# Get klines/candlesticks
klines = client.get_klines(
    symbol="BTC_USDC",
    interval="1h",
    limit=100
)

# Get recent trades
trades = client.get_recent_trades("BTC_USDC", num=50)
```

### Private Trading Operations (Authentication Required)

```python
# Get account balances
balances = client.get_balances()

# Place a futures order
order_id = client.place_order(
    symbol="btc_usdt",
    order_side="BUY",           # BUY or SELL
    order_type="LIMIT",         # LIMIT or MARKET
    position_side="LONG",       # LONG or SHORT
    quantity=100,               # Contract quantity
    price=70000.0,             # Limit price
    leverage=10,               # Leverage multiplier
    time_in_force="GTC",       # GTC, IOC, FOK, GTX
    reduce_only=False,         # Reduce-only order
    trigger_profit_price=75000, # Take profit price (optional)
    trigger_stop_price=68000    # Stop loss price (optional)
)

# Get order details
order = client.get_order_detail(order_id)

# Cancel order
cancelled_id = client.cancel_order(order_id)

# Batch cancel orders
results = client.batch_cancel_orders(["order_id_1", "order_id_2"])

# Query orders with filters
orders = client.get_orders(
    symbol="btc_usdt",
    state="UNFINISHED",  # UNFINISHED, HISTORY, CANCELED
    page=1,
    size=20
)

# Get order fills/executions
fills = client.get_order_fills(
    symbol="btc_usdt",
    page=1,
    size=20
)

# Get WebSocket listen key
listen_key = client.get_listen_key()
```

## Data Models

### Futures-Specific Models

```python
from sodex_api.futures import (
    FuturesBalance,      # Account balance information
    FuturesOrder,        # Order details
    FuturesOrderbook,    # Market depth
    FuturesPosition,     # Position information
    FuturesSymbol,       # Symbol/contract details
    FuturesTicker,       # 24hr ticker stats
    FuturesKline,        # Candlestick data
    FuturesTrade,        # Trade execution
    FuturesOrderFill,    # Order fill details
)

# Enumerations
from sodex_api.futures import (
    ContractType,    # PERPETUAL, DELIVERY
    PositionSide,    # LONG, SHORT
    OrderState,      # NEW, PARTIALLY_FILLED, FILLED, CANCELED, etc.
    TimeInForce,     # GTC, IOC, FOK, GTX
    PositionType     # CROSSED, ISOLATED
)
```

## Error Handling

The library now provides a comprehensive exception hierarchy:

```python
from sodex_api import (
    SodexAPIError,              # Base exception
    AuthenticationError,        # Auth failures
    RateLimitError,            # Rate limit exceeded
    InvalidOrderError,         # Invalid order parameters
    InsufficientBalanceError,  # Insufficient funds
    MarketDataError,           # Market data errors
    WebSocketError,            # WebSocket errors
)

try:
    order_id = client.place_order(...)
except InvalidOrderError as e:
    print(f"Invalid order: {e}")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except SodexAPIError as e:
    print(f"API error: {e}")
```

## Examples

See the `examples/futures/` directory for complete examples:

- `get_futures_balance.py` - Get account balances
- `place_futures_order.py` - Place a futures order
- `get_futures_ticker.py` - Get ticker information
- `get_futures_orderbook.py` - Get market depth
- `manage_futures_orders.py` - Comprehensive order management

## Differences from Spot Trading

1. **Position Management**: Futures orders require specifying `position_side` (LONG/SHORT)
2. **Leverage**: Futures support leverage trading (specify with `leverage` parameter)
3. **Contract Size**: Quantities are in contracts, not base currency
4. **Margin**: Orders freeze margin instead of the full notional value
5. **Advanced Orders**: Support for reduce-only orders, take profit, and stop loss

## Best Practices

1. **Error Handling**: Always wrap API calls in try-except blocks
2. **Rate Limiting**: Implement delays between requests to avoid rate limits
3. **Order Validation**: Validate order parameters before submission
4. **Position Monitoring**: Track your positions and margin levels
5. **Risk Management**: Use stop losses and appropriate leverage

## Migration from v1.x

The library maintains backward compatibility:

```python
# Old way (still works)
from sodex_api import SodexClient
client = SodexClient()

# New way (recommended)
from sodex_api import SpotClient, FuturesClient
spot_client = SpotClient()
futures_client = FuturesClient(...)
```

## API Rate Limits

- Public endpoints: 10 requests per second
- Private endpoints: 5 requests per second
- Batch operations count as single requests

## Support

For issues or questions:
- Check the examples in `examples/futures/`
- Review the API documentation
- Submit issues on GitHub