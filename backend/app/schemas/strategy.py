from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional, Any
from datetime import datetime

class BacktestRequest(BaseModel):
    symbol: str = Field(..., examples=["AAPL"])
    strategy: str = Field(..., examples=["MA_CROSSOVER"])
    period: str = Field(default="1y", examples=["1y"])
    interval: str = Field(default="1d", examples=["1d"])
    initial_capital: Optional[float] = Field(default=100000, examples=[100000])
    parameters: Optional[Dict[str, Any]] = Field(default={})
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "AAPL",
                "strategy": "MA_CROSSOVER",
                "period": "1y",
                "interval": "1d",
                "initial_capital": 100000,
                "parameters": {
                    "short_window": 20,
                    "long_window": 50
                }
            }
        }
    )

class EquityPoint(BaseModel):
    timestamp: datetime
    portfolio_value: float
    cash: float
    returns: float

class TradeRecord(BaseModel):
    timestamp: datetime
    type: str
    price: float
    quantity: float
    commission: float
    total: float
    pnl: Optional[float] = None
    cash_after: float

class BacktestMetrics(BaseModel):
    total_return: float
    total_return_percent: float
    winning_trades: int
    losing_trades: int
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    avg_trade_pnl: float
    avg_win: float
    avg_loss: float
    profit_factor: float

class BacktestResponse(BaseModel):
    strategy: str
    initial_capital: float
    final_portfolio_value: float
    total_return: float
    total_return_percent: float
    trades: List[TradeRecord]
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float
    equity_curve: List[EquityPoint]
    metrics: BacktestMetrics

class StrategyInfo(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    
class StrategyListResponse(BaseModel):
    strategies: List[StrategyInfo]