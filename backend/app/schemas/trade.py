from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from ..models.trade import OrderType, OrderStatus

class TradeBase(BaseModel):
    symbol: str = Field(..., description="Stock symbol")
    strategy: str = Field(..., description="Strategy name")
    order_type: OrderType
    quantity: float = Field(..., gt=0, description="Number of shares")
    price: float = Field(..., gt=0, description="Price per share")

class TradeCreate(TradeBase):
    pass

class TradeResponse(TradeBase):
    id: int
    commission: float
    status: OrderStatus
    timestamp: datetime
    pnl: float
    
    model_config = ConfigDict(from_attributes=True)

class TradeExecute(BaseModel):
    symbol: str
    strategy: str
    order_type: OrderType
    quantity: float
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "AAPL",
                "strategy": "MA_CROSSOVER",
                "order_type": "BUY",
                "quantity": 10
            }
        }
    )