import enum


class Chamber(str, enum.Enum):
    HOUSE = "house"
    SENATE = "senate"
    EXECUTIVE = "executive"


class TransactionType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"
    EXCHANGE = "exchange"


class SourceCode(str, enum.Enum):
    SENATE_STOCK_WATCHER = "senate_stock_watcher"
    HOUSE_STOCK_WATCHER = "house_stock_watcher"
    QUIVER_QUANT = "quiver_quant"
    SEC_EDGAR = "sec_edgar"


class RecommendationDirection(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class ConvictionLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
