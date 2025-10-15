from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from datetime import datetime
from ..core.database import Base

class Portfolio(Base):
    __tablename__ = "portfolio"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy = Column(String, index=True, nullable=False)
    cash = Column(Float, nullable=False)
    equity = Column(Float, nullable=False)  # Total portfolio value
    positions = Column(JSON, default={})  # {symbol: quantity}
    total_pnl = Column(Float, default=0.0)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Portfolio {self.strategy} Equity: ${self.equity:.2f}>"
    
    @property
    def win_rate(self):
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100