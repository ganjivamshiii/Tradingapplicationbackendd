from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from ..models.trade import Trade, OrderType, OrderStatus
from ..models.portfolio import Portfolio
from ..core.config import settings
from .data_feed import data_feed

class PortfolioManager:
    """Manages portfolio positions, cash, and PnL"""
    
    def __init__(self, db: Session, strategy: str, initial_capital: float = None):
        self.db = db
        self.strategy = strategy
        self.initial_capital = initial_capital or settings.INITIAL_CAPITAL
        self.commission_rate = settings.COMMISSION
        
        # Initialize or load portfolio
        self.portfolio = self._get_or_create_portfolio()
    
    def _get_or_create_portfolio(self) -> Portfolio:
        """Get existing portfolio or create new one"""
        portfolio = self.db.query(Portfolio).filter(
            Portfolio.strategy == self.strategy
        ).first()
        
        if not portfolio:
            portfolio = Portfolio(
                strategy=self.strategy,
                cash=self.initial_capital,
                equity=self.initial_capital,
                positions={},
                total_pnl=0.0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0
            )
            self.db.add(portfolio)
            self.db.commit()
            self.db.refresh(portfolio)
        
        return portfolio
    
    def execute_trade(
        self, 
        symbol: str, 
        order_type: OrderType, 
        quantity: float
    ) -> Trade:
        """Execute a trade and update portfolio"""
        
        # Get current price
        current_price = data_feed.get_latest_price(symbol)
        
        # Calculate commission
        commission = current_price * quantity * self.commission_rate
        
        # Calculate total cost
        total_cost = (current_price * quantity) + commission
        
        # Check if we have enough cash for BUY orders
        if order_type == OrderType.BUY:
            if self.portfolio.cash < total_cost:
                raise ValueError(f"Insufficient cash. Available: ${self.portfolio.cash:.2f}, Required: ${total_cost:.2f}")
        
        # Create trade record
        trade = Trade(
            symbol=symbol,
            strategy=self.strategy,
            order_type=order_type,
            quantity=quantity,
            price=current_price,
            commission=commission,
            status=OrderStatus.EXECUTED
        )
        
        # Update portfolio
        if order_type == OrderType.BUY:
            # Deduct cash
            self.portfolio.cash -= total_cost
            
            # Update positions
            positions = self.portfolio.positions or {}
            positions[symbol] = positions.get(symbol, 0) + quantity
            self.portfolio.positions = positions
            
        else:  # SELL
            # Check if we have the position
            positions = self.portfolio.positions or {}
            current_quantity = positions.get(symbol, 0)
            
            if current_quantity < quantity:
                raise ValueError(f"Insufficient {symbol} position. Have: {current_quantity}, Trying to sell: {quantity}")
            
            # Calculate PnL for this trade
            # Find average buy price from previous trades
            avg_buy_price = self._get_average_buy_price(symbol)
            pnl = (current_price - avg_buy_price) * quantity - commission
            trade.pnl = pnl
            
            # Add cash
            self.portfolio.cash += (current_price * quantity) - commission
            
            # Update positions
            positions[symbol] -= quantity
            if positions[symbol] == 0:
                del positions[symbol]
            self.portfolio.positions = positions
            
            # Update PnL stats
            self.portfolio.total_pnl += pnl
            if pnl > 0:
                self.portfolio.winning_trades += 1
            else:
                self.portfolio.losing_trades += 1
        
        # Update trade count
        self.portfolio.total_trades += 1
        
        # Calculate current equity
        self.portfolio.equity = self._calculate_equity()
        
        # Save to database
        self.db.add(trade)
        self.db.commit()
        self.db.refresh(trade)
        self.db.refresh(self.portfolio)
        
        return trade
    
    def _get_average_buy_price(self, symbol: str) -> float:
        """Calculate average buy price for a symbol"""
        buy_trades = self.db.query(Trade).filter(
            Trade.symbol == symbol,
            Trade.strategy == self.strategy,
            Trade.order_type == OrderType.BUY,
            Trade.status == OrderStatus.EXECUTED
        ).all()
        
        if not buy_trades:
            return 0.0
        
        total_cost = sum(t.price * t.quantity for t in buy_trades)
        total_quantity = sum(t.quantity for t in buy_trades)
        
        return total_cost / total_quantity if total_quantity > 0 else 0.0
    
    def _calculate_equity(self) -> float:
        """Calculate total portfolio equity (cash + positions value)"""
        equity = self.portfolio.cash
        
        positions = self.portfolio.positions or {}
        for symbol, quantity in positions.items():
            try:
                current_price = data_feed.get_latest_price(symbol)
                equity += current_price * quantity
            except Exception as e:
                print(f"Error getting price for {symbol}: {e}")
        
        return equity
    
    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio summary"""
        equity = self._calculate_equity()
        total_pnl = equity - self.initial_capital
        total_pnl_percent = (total_pnl / self.initial_capital) * 100
        
        return {
            'strategy': self.strategy,
            'cash': self.portfolio.cash,
            'equity': equity,
            'initial_capital': self.initial_capital,
            'total_pnl': total_pnl,
            'total_pnl_percent': total_pnl_percent,
            'positions': self.portfolio.positions or {},
            'total_trades': self.portfolio.total_trades,
            'winning_trades': self.portfolio.winning_trades,
            'losing_trades': self.portfolio.losing_trades,
            'win_rate': self.portfolio.win_rate
        }
    
    def get_position(self, symbol: str) -> float:
        """Get current position for a symbol"""
        positions = self.portfolio.positions or {}
        return positions.get(symbol, 0)
    
    def has_position(self, symbol: str) -> bool:
        """Check if we have an open position for a symbol"""
        return self.get_position(symbol) > 0