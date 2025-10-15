from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class OHLCV(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

class MarketDataRequest(BaseModel):
    symbol: str = Field(..., example="AAPL")
    period: str = Field(default="1mo", example="1mo")  # 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    interval: str = Field(default="1d", example="1d")  # 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo

class MarketDataResponse(BaseModel):
    symbol: str
    data: List[OHLCV]
    indicators: Optional[dict] = None

class SignalData(BaseModel):
    timestamp: datetime
    signal_type: str  # BUY, SELL, HOLD
    price: float
    reason: str

class StrategySignals(BaseModel):
    symbol: str
    strategy: str
    signals: List[SignalData]