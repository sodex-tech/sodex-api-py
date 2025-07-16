"""Data models for futures trading."""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class ContractType(Enum):
    """Contract type enumeration."""
    PERPETUAL = "PERPETUAL"
    DELIVERY = "DELIVERY"


class PositionSide(Enum):
    """Position side enumeration."""
    LONG = "LONG"
    SHORT = "SHORT"


class OrderState(Enum):
    """Order state enumeration."""
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class TimeInForce(Enum):
    """Time in force enumeration."""
    GTC = "GTC"  # Good Till Cancel
    IOC = "IOC"  # Immediate or Cancel
    FOK = "FOK"  # Fill or Kill
    GTX = "GTX"  # Good Till Crossing


class PositionType(Enum):
    """Position type enumeration."""
    CROSSED = "CROSSED"  # Cross margin
    ISOLATED = "ISOLATED"  # Isolated margin


@dataclass
class FuturesBalance:
    """Futures account balance information."""
    coin: str
    balance_type: str
    wallet_balance: float
    available_balance: float
    open_order_margin_frozen: float
    isolated_margin: float
    crossed_margin: float
    bonus: float


@dataclass
class FuturesSymbol:
    """Futures symbol information."""
    id: int
    symbol: str
    contract_type: str
    underlying_type: str
    contract_size: float
    init_leverage: int
    init_position_type: str
    base_coin: str
    quote_coin: str
    quantity_precision: int
    price_precision: int
    support_order_type: str
    support_time_in_force: str
    min_qty: float
    min_notional: float
    max_notional: float
    maker_fee: float
    taker_fee: float
    min_step_price: float
    trade_switch: bool
    state: int
    support_position_type: str
    max_open_orders: int
    max_entrusts: int
    liquidation_fee: float
    labels: Optional[List[str]] = None
    onboard_date: Optional[int] = None
    en_name: Optional[str] = None
    cn_name: Optional[str] = None


@dataclass
class FuturesOrder:
    """Futures order information."""
    order_id: str
    client_order_id: Optional[str]
    symbol: str
    contract_type: str
    order_type: str
    order_side: str
    leverage: int
    position_side: str
    time_in_force: str
    close_position: bool
    price: float
    orig_qty: float
    avg_price: float
    executed_qty: float
    margin_frozen: float
    trigger_profit_price: Optional[float]
    trigger_stop_price: Optional[float]
    source_id: Optional[str]
    force_close: bool
    trade_fee: float
    close_profit: Optional[float]
    state: str
    created_time: int
    updated_time: int


@dataclass
class FuturesOrderbook:
    """Futures orderbook data."""
    symbol: str
    timestamp: int
    update_id: int
    bids: List[List[float]]  # [[price, quantity], ...]
    asks: List[List[float]]  # [[price, quantity], ...]


@dataclass
class FuturesTicker:
    """Futures ticker data."""
    symbol: str
    timestamp: int
    close_price: float
    open_price: float
    high_price: float
    low_price: float
    volume: float
    quote_volume: float
    price_change_percent: float


@dataclass
class FuturesKline:
    """Futures kline/candlestick data."""
    symbol: str
    timestamp: int
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    quote_volume: float


@dataclass
class FuturesTrade:
    """Futures trade data."""
    symbol: str
    price: float
    quantity: float
    timestamp: int
    side: str  # "BID" or "ASK"


@dataclass
class FuturesOrderFill:
    """Futures order fill/execution data."""
    order_id: str
    exec_id: str
    symbol: str
    quantity: float
    price: float
    fee: float
    fee_coin: str
    timestamp: int


@dataclass
class FuturesPosition:
    """Futures position information."""
    symbol: str
    position_side: str
    position_type: str
    quantity: float
    entry_price: float
    mark_price: float
    unrealized_pnl: float
    realized_pnl: float
    margin: float
    leverage: int
    liquidation_price: Optional[float]
    auto_add_margin: bool
    created_time: int
    updated_time: int