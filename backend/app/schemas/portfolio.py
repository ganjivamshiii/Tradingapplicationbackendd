from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Dict
from typing import Optional

class PortfolioBase(BaseModel):
    strategy: str
    cash: float
    equity: float
    positions: Dict[str, float] = {}
    total_pnl: float = 0.0

class PortfolioCreate(PortfolioBase):
    pass

class PortfolioResponse(PortfolioBase):
    id: int
    total_trades: int
    winning_trades: int
    losing_trades: int
    timestamp: datetime
    win_rate: float
    
    model_config = ConfigDict(from_attributes=True)

class PortfolioSummary(BaseModel):
    strategy: str
    total_value: Optional[float] = None
    cash: Optional[float] = None
    invested: Optional[float] = None
    total_pnl: Optional[float] = None
    total_pnl_percent: Optional[float] = None
    win_rate: Optional[float] = None
    total_trades: Optional[int] = None
    positions: Dict[str, float] = {}
