"""Data models for spot trading."""

from dataclasses import dataclass, field
from typing import List, Optional, Literal
import time

OrderSide = Literal["BUY", "SELL"]
OrderType = Literal["LIMIT", "MARKET"]
OrderState = Literal["NEW", "PARTIALLY_FILLED", "FILLED", "CANCELED", "REJECTED", "EXPIRED"]


@dataclass
class OBItem:
    """Represents a single orderbook item (bid or ask)."""
    price: float
    quantity: float

    def __post_init__(self) -> None:
        """Validate orderbook item after initialization."""
        if self.price <= 0:
            raise ValueError("Price must be positive")
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")

    @property
    def notional_value(self) -> float:
        """Calculate the notional value (price * quantity)."""
        return self.price * self.quantity


@dataclass
class Orderbook:
    """Represents an orderbook snapshot from an exchange."""
    symbol: str
    timestamp: int
    bids: List[OBItem] = field(default_factory=list)
    asks: List[OBItem] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate orderbook after initialization."""
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
        if self.timestamp <= 0:
            raise ValueError("Timestamp must be positive")

    @property
    def best_bid(self) -> Optional[OBItem]:
        """Get the best bid (highest price)."""
        return max(self.bids, key=lambda x: x.price) if self.bids else None

    @property
    def best_ask(self) -> Optional[OBItem]:
        """Get the best ask (lowest price)."""
        return min(self.asks, key=lambda x: x.price) if self.asks else None

    @property
    def mid_price(self) -> Optional[float]:
        """Calculate the mid price between best bid and ask."""
        best_bid = self.best_bid
        best_ask = self.best_ask
        if best_bid and best_ask:
            return (best_bid.price + best_ask.price) / 2
        return None

    @property
    def spread_percentage(self) -> Optional[float]:
        """Calculate the spread as a percentage."""
        best_bid = self.best_bid
        best_ask = self.best_ask
        if best_bid and best_ask and self.mid_price:
            return (best_ask.price - best_bid.price) / self.mid_price
        return None

    @property
    def is_valid(self) -> bool:
        """Check if the orderbook has valid structure."""
        return bool(self.bids and self.asks and self.best_bid and self.best_ask)


@dataclass
class Balance:
    """Represents account balance for a specific asset."""
    symbol: str
    available: float
    locked: float = 0.0

    def __post_init__(self) -> None:
        """Validate balance after initialization."""
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
        if self.available < 0:
            raise ValueError("Available balance cannot be negative")
        if self.locked < 0:
            raise ValueError("Locked balance cannot be negative")

    @property
    def total(self) -> float:
        """Calculate total balance (available + locked)."""
        return self.available + self.locked

    def can_trade(self, required_amount: float) -> bool:
        """Check if there's sufficient available balance for trading."""
        return self.available >= required_amount


@dataclass
class Order:
    """Represents a trading order."""
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    type: str
    status: str
    timestamp: int
    client_order_id: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate order after initialization."""
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
        if self.side.upper() not in ('BUY', 'SELL'):
            raise ValueError("Side must be 'BUY' or 'SELL'")
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if self.price <= 0:
            raise ValueError("Price must be positive")
        self.side = self.side.upper()

    @property
    def notional_value(self) -> float:
        """Calculate the notional value of the order."""
        return self.price * self.quantity

    @property
    def is_buy(self) -> bool:
        """Check if this is a buy order."""
        return self.side == "BUY"

    @property
    def is_sell(self) -> bool:
        """Check if this is a sell order."""
        return self.side == "SELL"

    @property
    def is_active(self) -> bool:
        """Check if the order is in an active state."""
        active_statuses = {'NEW', 'PARTIALLY_FILLED', 'PENDING'}
        return self.status.upper() in active_statuses

    @property
    def age_seconds(self) -> float:
        """Calculate the age of the order in seconds."""
        return time.time() - (self.timestamp / 1000.0)  # Assuming timestamp is in milliseconds


@dataclass
class KlineData:
    """Represents kline/candlestick data."""
    symbol: str
    timestamp: int
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    quote_volume: float

    def __post_init__(self) -> None:
        """Validate kline data after initialization."""
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
        if self.timestamp <= 0:
            raise ValueError("Timestamp must be positive")
        if any(price <= 0 for price in [self.open_price, self.high_price, self.low_price, self.close_price]):
            raise ValueError("All prices must be positive")
        if self.volume < 0:
            raise ValueError("Volume cannot be negative")
        if self.quote_volume < 0:
            raise ValueError("Quote volume cannot be negative")

    @property
    def price_change(self) -> float:
        """Calculate price change from open to close."""
        return self.close_price - self.open_price

    @property
    def price_change_percent(self) -> float:
        """Calculate price change percentage."""
        if self.open_price == 0:
            return 0.0
        return (self.price_change / self.open_price) * 100

    @property
    def is_bullish(self) -> bool:
        """Check if the kline is bullish (close > open)."""
        return self.close_price > self.open_price

    @property
    def is_bearish(self) -> bool:
        """Check if the kline is bearish (close < open)."""
        return self.close_price < self.open_price


@dataclass
class TickerData:
    """Represents 24hr ticker price change statistics."""
    symbol: str
    timestamp: int
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    quote_volume: float
    price_change_percent: float

    def __post_init__(self) -> None:
        """Validate ticker data after initialization."""
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
        if self.timestamp <= 0:
            raise ValueError("Timestamp must be positive")
        if any(price <= 0 for price in [self.open_price, self.high_price, self.low_price, self.close_price]):
            raise ValueError("All prices must be positive")
        if self.volume < 0:
            raise ValueError("Volume cannot be negative")
        if self.quote_volume < 0:
            raise ValueError("Quote volume cannot be negative")

    @property
    def price_change(self) -> float:
        """Calculate absolute price change."""
        return self.close_price - self.open_price

    @property
    def is_up(self) -> bool:
        """Check if price is up from 24h ago."""
        return self.price_change_percent > 0

    @property
    def is_down(self) -> bool:
        """Check if price is down from 24h ago."""
        return self.price_change_percent < 0


@dataclass
class TradeData:
    """Represents a recent trade."""
    symbol: str
    timestamp: int
    price: float
    quantity: float
    side: str

    def __post_init__(self) -> None:
        """Validate trade data after initialization."""
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
        if self.timestamp <= 0:
            raise ValueError("Timestamp must be positive")
        if self.price <= 0:
            raise ValueError("Price must be positive")
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if not self.side:
            raise ValueError("Side cannot be empty")

    @property
    def notional_value(self) -> float:
        """Calculate the notional value of the trade."""
        return self.price * self.quantity

    @property
    def is_buy(self) -> bool:
        """Check if this is a buy trade."""
        return self.side.upper() in ('BUY', 'BID')

    @property
    def is_sell(self) -> bool:
        """Check if this is a sell trade."""
        return self.side.upper() in ('SELL', 'ASK')


@dataclass
class OrderFill:
    """Represents an order fill/execution."""
    order_id: str
    exec_id: str
    symbol: str
    quantity: float
    price: float
    fee: float
    fee_coin: str
    side: str
    timestamp: int

    def __post_init__(self) -> None:
        """Validate order fill after initialization."""
        if not self.order_id:
            raise ValueError("Order ID cannot be empty")
        if not self.exec_id:
            raise ValueError("Execution ID cannot be empty")
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if self.price <= 0:
            raise ValueError("Price must be positive")
        if self.fee < 0:
            raise ValueError("Fee cannot be negative")
        if not self.fee_coin:
            raise ValueError("Fee coin cannot be empty")
        if self.side.upper() not in ('BUY', 'SELL'):
            raise ValueError("Side must be 'BUY' or 'SELL'")
        if self.timestamp <= 0:
            raise ValueError("Timestamp must be positive")

    @property
    def notional_value(self) -> float:
        """Calculate the notional value of the fill."""
        return self.price * self.quantity

    @property
    def is_buy(self) -> bool:
        """Check if this is a buy fill."""
        return self.side.upper() == 'BUY'

    @property
    def is_sell(self) -> bool:
        """Check if this is a sell fill."""
        return self.side.upper() == 'SELL'


@dataclass
class SymbolInfo:
    """Represents trading symbol information."""
    id: int
    symbol: str
    name: Optional[str]
    lever: Optional[float]
    risk_rate: Optional[float]
    trade_switch: bool
    buy_coin: str
    sell_coin: str
    buy_coin_precision: int
    buy_coin_display_precision: int
    sell_coin_precision: int
    sell_coin_display_precision: int
    quantity_precision: int
    price_precision: int
    support_order_type: str
    support_time_in_force: str
    min_price: Optional[float]
    min_qty: str
    min_notional: Optional[float]
    multiplier_down: str
    multiplier_up: str
    maker_fee: str
    taker_fee: str
    market_take_bound: str
    depth_precision_merge: int
    onboard_date: int
    sequence: int
    set_type: int
    uids: Optional[str]
    hot: bool

    def __post_init__(self) -> None:
        """Validate symbol info after initialization."""
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
        if not self.buy_coin:
            raise ValueError("Buy coin cannot be empty")
        if not self.sell_coin:
            raise ValueError("Sell coin cannot be empty")
        if self.buy_coin_precision < 0:
            raise ValueError("Buy coin precision cannot be negative")
        if self.sell_coin_precision < 0:
            raise ValueError("Sell coin precision cannot be negative")
        if self.quantity_precision < 0:
            raise ValueError("Quantity precision cannot be negative")
        if self.price_precision < 0:
            raise ValueError("Price precision cannot be negative")

    @property
    def is_active(self) -> bool:
        """Check if trading is enabled for this symbol."""
        return self.trade_switch

    @property
    def supported_order_types(self) -> List[str]:
        """Get list of supported order types."""
        return [ot.strip() for ot in self.support_order_type.split(',') if ot.strip()]

    @property
    def supported_time_in_force(self) -> List[str]:
        """Get list of supported time in force options."""
        return [tif.strip() for tif in self.support_time_in_force.split(',') if tif.strip()]

    @property
    def min_quantity(self) -> float:
        """Get minimum quantity as float."""
        try:
            return float(self.min_qty)
        except (ValueError, TypeError):
            return 0.0

    @property
    def maker_fee_rate(self) -> float:
        """Get maker fee rate as float."""
        try:
            return float(self.maker_fee)
        except (ValueError, TypeError):
            return 0.0

    @property
    def taker_fee_rate(self) -> float:
        """Get taker fee rate as float."""
        try:
            return float(self.taker_fee)
        except (ValueError, TypeError):
            return 0.0


# WebSocket specific models
@dataclass
class DepthData:
    """Represents depth/orderbook update data."""
    id: str
    symbol: str
    side: Literal["ASK", "BID"]
    price: float
    quantity: float
    timestamp: int


@dataclass
class KlineStreamData:
    """Represents kline stream data."""
    symbol: str
    open_price: float
    close_price: float
    high_price: float
    low_price: float
    volume: float
    quote_volume: float
    interval: str
    timestamp: int


@dataclass
class UserBalanceData:
    """Represents user balance update data."""
    coin: str
    balance_type: int
    balance: float
    freeze: float
    available_balance: float
    estimated_total_amount: float
    estimated_cny_amount: float
    estimated_available_amount: float
    estimated_coin_type: str


@dataclass
class UserOrderData:
    """Represents user order update data."""
    order_id: str
    balance_type: int
    order_type: OrderSide
    symbol: str
    price: float
    direction: OrderSide
    orig_qty: float
    avg_price: float
    executed_qty: float
    state: int  # 1=new, 2=partial, 3=filled, 4=cancelled
    create_time: int


@dataclass
class UserTradeData:
    """Represents user trade execution data."""
    order_id: str
    price: float
    quantity: float
    margin_unfrozen: float
    timestamp: int


@dataclass
class SystemMessage:
    """Represents system notification message."""
    id: int
    title: str
    content: str
    agg_type: str
    detail_type: str
    created_time: int
    all_scope: bool
    user_id: int
    read: bool