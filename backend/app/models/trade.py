from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from datetime import datetime
import enum
from ..core.database import Base

class OrderType(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    strategy = Column(String, index=True, nullable=False)
    order_type = Column(Enum(OrderType), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    commission = Column(Float, default=0.0)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    timestamp = Column(DateTime, default=datetime.utcnow)
    pnl = Column(Float, default=0.0)  # Profit/Loss for this trade
    
    def __repr__(self):
        return f"<Trade {self.order_type} {self.quantity} {self.symbol} @ {self.price}>"